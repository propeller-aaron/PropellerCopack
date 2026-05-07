const SMTP2GO_SEND_ENDPOINT = "https://api.smtp2go.com/v3/email/send";
const CONTACT_REQUEST_SUBJECT = "Contact Request from propellercopack.com";
const CONTACT_REQUEST_SENDER = "msg@propellercopack.com";

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type"
    }
  });
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type"
        }
      });
    }

    if (request.method !== "POST") {
      return jsonResponse({ error: "Method not allowed." }, 405);
    }

    if (!env.SMTP2GO_API_KEY) {
      return jsonResponse({ error: "Server is not configured." }, 500);
    }

    let payload;
    try {
      payload = await request.json();
    } catch {
      return jsonResponse({ error: "Invalid JSON payload." }, 400);
    }

    const { name, email, message, marketingOptIn } = payload;
    if (!name || !email || !message) {
      return jsonResponse(
        { error: "Missing required fields: name, email, message." },
        400
      );
    }

    const recipient = env.CONTACT_REQUEST_RECIPIENT || CONTACT_REQUEST_SENDER;
    const textBody = [
      `Name: ${name}`,
      `Email: ${email}`,
      `Marketing Opt-In: ${marketingOptIn ? "Yes" : "No"}`,
      "",
      "Message:",
      String(message)
    ].join("\n");

    const smtpPayload = {
      api_key: env.SMTP2GO_API_KEY,
      to: [recipient],
      sender: CONTACT_REQUEST_SENDER,
      subject: CONTACT_REQUEST_SUBJECT,
      reply_to: [email],
      text_body: textBody
    };

    const smtpResponse = await fetch(SMTP2GO_SEND_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(smtpPayload)
    });

    const smtpResult = await smtpResponse.json();

    if (!smtpResponse.ok || smtpResult?.data?.succeeded !== 1) {
      const message = smtpResult?.data?.error || smtpResult?.error || "SMTP2GO send failed.";
      return jsonResponse({ error: message }, 502);
    }

    return jsonResponse({ ok: true, message: "Email sent." }, 200);
  }
};
