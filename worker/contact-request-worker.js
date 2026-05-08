const SMTP2GO_SEND_ENDPOINT = "https://api.smtp2go.com/v3/email/send";
const CONTACT_REQUEST_SUBJECT = "Propeller Co-Pack Online Inquiry";
const CONTACT_REQUEST_SENDER = "inquiry@propellercopack.com";

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

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
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

    const { name, company, phone, email, message, marketingOptIn } = payload;
    if (!name || !company || !phone || !email || !message) {
      return jsonResponse(
        {
          error:
            "Missing required fields: name, company, phone, email, message."
        },
        400
      );
    }

    const recipient = env.CONTACT_REQUEST_RECIPIENT || CONTACT_REQUEST_SENDER;

    const textBody = [
      `Name: ${name}`,
      `Company: ${company}`,
      `Phone: ${phone}`,
      `Email: ${email}`,
      `Marketing Opt-In: ${marketingOptIn ? "Yes" : "No"}`,
      "",
      "Message:",
      String(message)
    ].join("\n");

    const htmlBody = `
      <div style="font-family: Arial, sans-serif; line-height: 1.5; padding: 10px;">
        <h2 style="margin-bottom: 10px;">New Online Inquiry</h2>
        <p><strong>Name:</strong> ${escapeHtml(name)}</p>
        <p><strong>Company:</strong> ${escapeHtml(company)}</p>
        <p><strong>Phone:</strong> ${escapeHtml(phone)}</p>
        <p><strong>Email:</strong> ${escapeHtml(email)}</p>
        <p><strong>Marketing Opt-In:</strong> ${marketingOptIn ? "Yes" : "No"}</p>
        <hr style="margin: 20px 0;">
        <p><strong>Message:</strong></p>
        <p>${escapeHtml(String(message)).replace(/\n/g, "<br>")}</p>
      </div>
    `;

    const smtpPayload = {
      api_key: env.SMTP2GO_API_KEY,
      to: [recipient],
      sender: CONTACT_REQUEST_SENDER,
      subject: CONTACT_REQUEST_SUBJECT,
      reply_to: [email],
      text_body: textBody,
      html_body: htmlBody
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
      const messageText =
        smtpResult?.data?.error || smtpResult?.error || "SMTP2GO send failed.";
      return jsonResponse({ error: messageText }, 502);
    }

    return jsonResponse({ ok: true, message: "Email sent." }, 200);
  }
};
