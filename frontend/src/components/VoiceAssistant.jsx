
import React, { useState } from "react";

function VoiceAssistant() {
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  // TEXT TO SPEECH
  const speak = async (text) => {
    const params = new URLSearchParams({
      text: text,
      language: "en"
    });

    const res = await fetch(
      `http://127.0.0.1:8000/api/voice/text-to-speech?${params}`,
      {
        method: "POST"
      }
    );

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error("TTS Error: " + errorText);
    }

    const blob = await res.blob();
    const audioUrl = URL.createObjectURL(blob);
    const audio = new Audio(audioUrl);

    audio.onended = () => {
      URL.revokeObjectURL(audioUrl);
    };

    await audio.play();
  };

  // SEND MESSAGE TO GEMINI
  const sendMessage = async (text) => {
    if (!text.trim()) return;

    setLoading(true);

    try {
      const res = await fetch(
        "http://127.0.0.1:8000/api/voice/voice-chat",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            text: text,
            session_id: sessionId
          })
        }
      );

      if (!res.ok) {
        throw new Error(await res.text());
      }

      const data = await res.json();

      setSessionId(data.session_id);
      setResponse(data.ai_response);

      await speak(data.ai_response);

    } catch (error) {
      console.error("VOICE ASSISTANT ERROR:", error);
      setResponse("Sorry, something went wrong: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  // SPEECH TO TEXT
  const startListening = () => {
    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech recognition is not supported.");
      return;
    }

    const recognition = new SpeechRecognition();

    recognition.lang = "en-IN";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (event) => {
      const text = event.results[0][0].transcript;

      setMessage(text);
      sendMessage(text);
    };

    recognition.onerror = (event) => {
      setResponse("Microphone error: " + event.error);
    };

    recognition.start();
  };

  return (
    <div style={{ padding: 30 }}>
      <h2>AI Doctor Voice Assistant</h2>

      <button onClick={startListening} disabled={loading}>
        🎤 Speak
      </button>

      <p>{loading ? "AI is thinking..." : ""}</p>

      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type your message"
      />

      <button
        onClick={() => sendMessage(message)}
        disabled={loading}
      >
        Send
      </button>

      <h3>AI Response</h3>
      <p>{response}</p>
    </div>
  );
}

export default VoiceAssistant;
