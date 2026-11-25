
import React, { useEffect, useState, useCallback } from "react";
import "../App.css";

const API_URL = "http://127.0.0.1:8000";

// Safely read JSON responses
async function readResponse(response, defaultMessage) {
  const data = await response.json().catch(() => ({}));

  if (response.status === 401 || response.status === 403) {
    localStorage.removeItem("admin_token");
    window.location.href = "/admin-login";
    throw new Error("Session expired. Please login again.");
  }

  if (!response.ok || data.success === false) {
    throw new Error(data.detail || data.message || defaultMessage);
  }

  return data;
}

// Admin authentication headers
const getAuthHeaders = () => {
  const token = localStorage.getItem("admin_token");

  if (!token) {
    window.location.href = "/admin-login";
    throw new Error("Please login as admin");
  }

  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
};




function Dashboard() {
  const [doctors, setDoctors] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [cancellingId, setCancellingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  // Search and filters
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [doctorFilter, setDoctorFilter] = useState("all");
  const [dateFilter, setDateFilter] = useState("");

  // Edit appointment
  const [editingAppointment, setEditingAppointment] = useState(null);
  const [editDoctorId, setEditDoctorId] = useState("");
  const [editSlotId, setEditSlotId] = useState("");
  const [availableSlots, setAvailableSlots] = useState([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editError, setEditError] = useState("");

  // Fetch dashboard data
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const headers = getAuthHeaders();

      const [doctorResponse, appointmentResponse] = await Promise.all([
        fetch(`${API_URL}/api/doctors/`, { headers }),
        fetch(`${API_URL}/api/appointments/`, { headers }),
      ]);

      const doctorData = await readResponse(
        doctorResponse,
        "Unable to fetch doctors"
      );

      const appointmentData = await readResponse(
        appointmentResponse,
        "Unable to fetch appointments"
      );

      if (!Array.isArray(doctorData) || !Array.isArray(appointmentData)) {
        throw new Error("Invalid dashboard data received from server");
      }

      setDoctors(doctorData);
      setAppointments(appointmentData);
    } catch (err) {
      console.error("Dashboard error:", err);
      setError(err.message || "Unable to load dashboard data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Statistics
  const booked = appointments.filter(
    (appointment) => appointment.status === "booked"
  );

  const cancelled = appointments.filter(
    (appointment) => appointment.status === "cancelled"
  );

  // Search and filter appointments
  const filteredAppointments = appointments.filter((appointment) => {
    const searchText = search.toLowerCase().trim();
    const patientName = (appointment.patient_name || "").toLowerCase();
    const phoneNumber = String(appointment.phone_number || "");

    const searchMatch =
      patientName.includes(searchText) ||
      phoneNumber.includes(searchText);

    const statusMatch =
      statusFilter === "all" ||
      appointment.status === statusFilter;

    const doctorMatch =
      doctorFilter === "all" ||
      appointment.doctor_name === doctorFilter;

    const dateMatch =
      !dateFilter ||
      String(appointment.date || "").slice(0, 10) === dateFilter;

    return searchMatch && statusMatch && doctorMatch && dateMatch;
  });

  // Clear filters
  const clearFilters = () => {
    setSearch("");
    setStatusFilter("all");
    setDoctorFilter("all");
    setDateFilter("");
  };

  // Cancel appointment
  const cancelAppointment = async (appointment) => {
    const confirmed = window.confirm(
      `Cancel appointment ID ${appointment.appointment_id} for ${appointment.patient_name}?`
    );

    if (!confirmed) return;

    setCancellingId(appointment.appointment_id);

    try {
      const response = await fetch(
        `${API_URL}/api/appointments/${appointment.appointment_id}/status`,
        {
          method: "PATCH",
          headers: getAuthHeaders(),
          body: JSON.stringify({
            status: "cancelled",
          }),
        }
      );

      await readResponse(response, "Appointment cancellation failed");

      window.alert("Appointment cancelled successfully!");
      await fetchData();
    } catch (err) {
      console.error("Cancellation error:", err);
      window.alert(err.message || "Cancellation failed");
    } finally {
      setCancellingId(null);
    }
  };

  // Delete cancelled appointment
  const deleteAppointment = async (appointmentId) => {
    const confirmed = window.confirm(
      "Permanently delete this cancelled appointment?"
    );

    if (!confirmed) return;

    setDeletingId(appointmentId);

    try {
      const response = await fetch(
        `${API_URL}/api/appointments/${appointmentId}`,
        {
          method: "DELETE",
          headers: getAuthHeaders(),
        }
      );

      await readResponse(response, "Unable to delete appointment");

      window.alert("Appointment deleted successfully!");
      await fetchData();
    } catch (err) {
      console.error("Delete error:", err);
      window.alert(err.message || "Unable to delete appointment");
    } finally {
      setDeletingId(null);
    }
  };

  // Fetch slots for selected doctor
  const fetchAvailableSlots = async (doctorId, currentSlotId = null) => {
    if (!doctorId) {
      setAvailableSlots([]);
      setEditSlotId("");
      return;
    }

    setSlotsLoading(true);
    setEditError("");
    setAvailableSlots([]);
    setEditSlotId("");

    try {
      const response = await fetch(
        `${API_URL}/api/doctors/${doctorId}/slots`,
        {
          headers: getAuthHeaders(),
        }
      );

      const data = await readResponse(
        response,
        "Unable to fetch doctor slots"
      );

      if (!Array.isArray(data)) {
        throw new Error("Invalid slots response from server");
      }

      const usableSlots = data.filter(
        (slot) =>
          slot.status === "available" ||
          Number(slot.id) === Number(currentSlotId)
      );

      setAvailableSlots(usableSlots);
    } catch (err) {
      console.error("Slot loading error:", err);
      setEditError(err.message || "Unable to load slots");
    } finally {
      setSlotsLoading(false);
    }
  };

  // Open edit modal
  const startEditing = (appointment) => {
    setEditingAppointment(appointment);
    setEditDoctorId(String(appointment.doctor_id || ""));
    setEditSlotId("");
    setAvailableSlots([]);
    setEditError("");

    fetchAvailableSlots(
      appointment.doctor_id,
      appointment.slot_id
    );
  };

  // Close edit modal
  const closeEditModal = () => {
    if (saving) return;

    setEditingAppointment(null);
    setEditDoctorId("");
    setEditSlotId("");
    setAvailableSlots([]);
    setEditError("");
  };

  // Change doctor
  const handleDoctorChange = (event) => {
    const doctorId = event.target.value;

    setEditDoctorId(doctorId);
    setEditSlotId("");

    fetchAvailableSlots(doctorId);
  };

  // Save appointment changes
  const saveAppointment = async (event) => {
    event.preventDefault();

    if (!editingAppointment) return;

    if (!editDoctorId || !editSlotId) {
      setEditError("Please select a doctor and an available slot.");
      return;
    }

    setSaving(true);
    setEditError("");

    try {
      const response = await fetch(
        `${API_URL}/api/appointments/${editingAppointment.appointment_id}/edit`,
        {
          method: "PUT",
          headers: getAuthHeaders(),
          body: JSON.stringify({
            doctor_id: Number(editDoctorId),
            slot_id: Number(editSlotId),
          }),
        }
      );

      await readResponse(response, "Unable to update appointment");

      window.alert("Appointment updated successfully!");

      setEditingAppointment(null);
      setEditDoctorId("");
      setEditSlotId("");
      setAvailableSlots([]);

      await fetchData();
    } catch (err) {
      console.error("Update appointment error:", err);
      setEditError(err.message || "Appointment update failed");
    } finally {
      setSaving(false);
    }
  };

  // Loading screen
  if (loading) {
    return (
      <div className="loading-screen">
        <h2>Loading Hospital Dashboard...</h2>
      </div>
    );
  }

  return (
    <div className="dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div>
          <h1>Hospital Admin Dashboard</h1>
          <p>Manage doctors and patient appointments</p>
        </div>

        <button
          className="logout-btn"
          onClick={() => {
            localStorage.removeItem("admin_token");
            window.location.href = "/admin-login";
          }}
        >
          Logout
        </button>

        <button
          className="refresh-btn"
          onClick={fetchData}
          disabled={loading}
        >
          ↻ Refresh Data
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="error-message">
          {error}
          <button onClick={fetchData}>Try Again</button>
        </div>
      )}

      {/* Statistics */}
      <div className="stats-grid">
        <Stat title="Total Doctors" value={doctors.length} color="blue" />
        <Stat
          title="Total Appointments"
          value={appointments.length}
          color="purple"
        />
        <Stat title="Booked Appointments" value={booked.length} color="green" />
        <Stat
          title="Cancelled Appointments"
          value={cancelled.length}
          color="red"
        />
      </div>

      {/* Doctors */}
      <section className="dashboard-section">
        <h2>Doctors List</h2>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Doctor Name</th>
                <th>Speciality</th>
                <th>Experience</th>
              </tr>
            </thead>

            <tbody>
              {doctors.length > 0 ? (
                doctors.map((doctor) => (
                  <tr key={doctor.id}>
                    <td>{doctor.id}</td>
                    <td>{doctor.name}</td>
                    <td>{doctor.speciality}</td>
                    <td>{doctor.experience} years</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="4">No doctors found</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Appointment Management */}
      <section className="appointment-management">
        <div className="section-header">
          <div>
            <h2>Appointment Management</h2>
            <p>Search, filter and manage patient appointments</p>
          </div>
        </div>

        {/* Filters */}
        <div className="filter-container">
          <input
            type="text"
            placeholder="Search patient or phone number"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />

          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
          >
            <option value="all">All Status</option>
            <option value="booked">Booked</option>
            <option value="cancelled">Cancelled</option>
          </select>

          <select
            value={doctorFilter}
            onChange={(event) => setDoctorFilter(event.target.value)}
          >
            <option value="all">All Doctors</option>
            {doctors.map((doctor) => (
              <option key={doctor.id} value={doctor.name}>
                {doctor.name}
              </option>
            ))}
          </select>

          <input
            type="date"
            value={dateFilter}
            onChange={(event) => setDateFilter(event.target.value)}
          />

          <button className="clear-btn" onClick={clearFilters}>
            Clear Filters
          </button>
        </div>

        <div className="appointment-count">
          Showing <strong>{filteredAppointments.length}</strong> of{" "}
          <strong>{appointments.length}</strong> appointments
        </div>

        {/* Appointment Table */}
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Patient</th>
                <th>Phone</th>
                <th>Doctor</th>
                <th>Date</th>
                <th>Time</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              {filteredAppointments.length > 0 ? (
                filteredAppointments.map((appointment) => (
                  <tr key={appointment.appointment_id}>
                    <td>{appointment.appointment_id}</td>
                    <td>{appointment.patient_name}</td>
                    <td>{appointment.phone_number}</td>
                    <td>{appointment.doctor_name || "N/A"}</td>
                    <td>{appointment.date}</td>
                    <td>{appointment.time}</td>

                    <td>
                      <span
                        className={
                          appointment.status === "booked"
                            ? "status-booked"
                            : "status-cancelled"
                        }
                      >
                        {appointment.status}
                      </span>
                    </td>

                    <td className="action-buttons">
                      {appointment.status === "booked" ? (
                        <>
                          <button
                            className="edit-btn"
                            onClick={() => startEditing(appointment)}
                            disabled={saving}
                          >
                            Edit
                          </button>

                          <button
                            className="cancel-btn"
                            onClick={() => cancelAppointment(appointment)}
                            disabled={
                              cancellingId === appointment.appointment_id
                            }
                          >
                            {cancellingId === appointment.appointment_id
                              ? "Cancelling..."
                              : "Cancel"}
                          </button>
                        </>
                      ) : (
                        <>
                          <span className="already-cancelled">
                            Cancelled
                          </span>

                          <button
                            className="delete-btn"
                            onClick={() =>
                              deleteAppointment(appointment.appointment_id)
                            }
                            disabled={
                              deletingId === appointment.appointment_id
                            }
                          >
                            {deletingId === appointment.appointment_id
                              ? "Deleting..."
                              : "Delete"}
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="8" className="no-data">
                    No appointments found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Edit Appointment Modal */}
      {editingAppointment && (
        <div className="edit-modal-overlay">
          <div
            className="edit-modal-content"
            role="dialog"
            aria-modal="true"
            aria-labelledby="edit-appointment-title"
          >
            <h2 id="edit-appointment-title">Edit Appointment</h2>

            <p>
              Patient: <strong>{editingAppointment.patient_name}</strong>
            </p>

            <p>
              Appointment ID:{" "}
              <strong>{editingAppointment.appointment_id}</strong>
            </p>

            <form onSubmit={saveAppointment}>
              <label htmlFor="edit-doctor">Select Doctor</label>

              <select
                id="edit-doctor"
                value={editDoctorId}
                onChange={handleDoctorChange}
                required
                disabled={saving}
              >
                <option value="">Choose a doctor</option>

                {doctors.map((doctor) => (
                  <option key={doctor.id} value={doctor.id}>
                    {doctor.name} - {doctor.speciality}
                  </option>
                ))}
              </select>

              <label htmlFor="edit-slot">Select Available Slot</label>

              <select
                id="edit-slot"
                value={editSlotId}
                onChange={(event) => setEditSlotId(event.target.value)}
                required
                disabled={saving || slotsLoading || !editDoctorId}
              >
                <option value="">
                  {slotsLoading
                    ? "Loading slots..."
                    : "Choose an available slot"}
                </option>

                {availableSlots.map((slot) => (
                  <option key={slot.id} value={slot.id}>
                    {slot.date} - {slot.time}
                    {Number(slot.id) ===
                    Number(editingAppointment.slot_id)
                      ? " (Current slot)"
                      : ""}
                  </option>
                ))}
              </select>

              {!slotsLoading &&
                editDoctorId &&
                availableSlots.length === 0 && (
                  <p className="edit-help">
                    No available slots found for this doctor.
                  </p>
                )}

              {editError && (
                <p className="edit-error">{editError}</p>
              )}

              <div className="edit-modal-actions">
                <button
                  type="button"
                  className="close-btn"
                  onClick={closeEditModal}
                  disabled={saving}
                >
                  Close
                </button>

                <button
                  type="submit"
                  className="save-btn"
                  disabled={
                    saving ||
                    slotsLoading ||
                    !editDoctorId ||
                    !editSlotId
                  }
                >
                  {saving ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// Statistics card
function Stat({ title, value, color }) {
  return (
    <div className={`stat-card ${color}`}>
      <h3>{title}</h3>
      <h1>{value}</h1>
    </div>
  );
}

export default Dashboard;
