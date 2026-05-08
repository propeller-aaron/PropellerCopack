(function () {
  const measurementId = "G-WFT2TFB1EX";
  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () {
    window.dataLayer.push(arguments);
  };
  window.gtag("js", new Date());
  window.gtag("config", measurementId);

  if (!document.querySelector('script[src*="googletagmanager.com/gtag/js"]')) {
    const gtagScript = document.createElement("script");
    gtagScript.async = true;
    gtagScript.src =
      "https://www.googletagmanager.com/gtag/js?id=" + measurementId;
    document.head.appendChild(gtagScript);
  }
})();

(function () {
  const WORKER_SEND_ENDPOINT = "https://prop-copack-form.aaron-4d8.workers.dev";

  const form = document.getElementById("contactForm");
  const statusEl = document.getElementById("status");
  if (!form) return;
  const submitBtn = form.querySelector('button[type="submit"]');
  const defaultSubmitText = submitBtn ? submitBtn.textContent : "Submit";

  function setSubmittingState(isSubmitting) {
    if (!submitBtn) return;
    submitBtn.disabled = isSubmitting;
    if (isSubmitting) {
      submitBtn.innerHTML =
        '<span class="propeller-submit-spinner" aria-hidden="true"></span>Sending...';
    } else {
      submitBtn.textContent = defaultSubmitText;
    }
  }

  function showThankYou() {
    const wrap = form.closest(".propeller-form-wrap");
    if (!wrap) return;
    const targetHeight = 210;

    form.classList.add("is-complete");
    wrap.classList.add("is-complete-state");
    if (targetHeight > 0) {
      wrap.style.minHeight = targetHeight + "px";
    }
    if (statusEl) statusEl.textContent = "";

    window.setTimeout(function () {
      form.style.display = "none";

      let thankYou = wrap.querySelector(".propeller-thankyou");
      if (!thankYou) {
        thankYou = document.createElement("div");
        thankYou.className = "propeller-thankyou";
        thankYou.innerHTML = [
          "<h3>Thank you for reaching out.</h3>",
          "<p>We appreciate the opportunity to learn about your product, packaging, and production goals. A Propeller team member will follow up soon.</p>"
        ].join("");
        wrap.appendChild(thankYou);
      }
      if (targetHeight > 0) {
        thankYou.style.minHeight = targetHeight + "px";
      }
    }, 350);
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    setSubmittingState(true);

    const formData = new FormData(form);

    const payload = {
      name: formData.get("name"),
      company: formData.get("company"),
      phone: formData.get("phone"),
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

      showThankYou();
    } catch (error) {
      console.error("Contact form submission failed:", error);
      setSubmittingState(false);
    }
  });
})();
