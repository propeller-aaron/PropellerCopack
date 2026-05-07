(function () {
  const WORKER_SEND_ENDPOINT = "https://prop-copack-form.aaron-4d8.workers.dev";

  const form = document.getElementById("contactForm");
  const statusEl = document.getElementById("status");
  if (!form || !statusEl) return;

  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    statusEl.textContent = "Sending...";

    const formData = new FormData(form);

    const payload = {
      name: formData.get("name"),
      email: formData.get("email"),
      message: formData.get("message"),
      marketingOptIn: formData.get("marketingOptIn") === "on"
    };

    try {
      const response = await fetch(WORKER_SEND_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const result = await response.json();

      if (!response.ok || result?.ok !== true) {
        const errorMessage =
          result?.message || result?.error || "Failed to submit form.";
        throw new Error(errorMessage);
      }

      statusEl.textContent = "Form submitted successfully.";
      form.reset();
    } catch (error) {
      statusEl.textContent = "Error: " + error.message;
    }
  });
})();
