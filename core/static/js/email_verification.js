document.addEventListener("DOMContentLoaded", () => {
    const inputs = document.querySelectorAll(".input-field input");
    const button = document.querySelector("form button");
    const countdownElement = document.getElementById("countdown");
    const requestCodeLink = document.getElementById("requestCodeLink");
    let remainingTime = parseInt(countdownElement.textContent, 10);
  
    // Function to manage countdown timer
    const startCountdown = () => {
      const timer = setInterval(() => {
        if (remainingTime > 0) {
          remainingTime--;
          countdownElement.textContent = remainingTime;
        } else {
          clearInterval(timer);
          countdownElement.textContent = "Expired";
          requestCodeLink.textContent = "Resend code";
          requestCodeLink.style.cursor = "pointer";
          requestCodeLink.style.color = "#4070f4";
          requestCodeLink.style.textDecoration = "underline";
        }
      }, 1000);
    };
  
    // Start the countdown on page load
    startCountdown();
  
    // OTP input behavior
    inputs.forEach((input, index1) => {
      input.addEventListener("keyup", (e) => {
        const currentInput = input;
        const nextInput = input.nextElementSibling;
        const prevInput = input.previousElementSibling;
  
        // Allow only one digit per input
        if (currentInput.value.length > 1) {
          currentInput.value = currentInput.value[0];
        }
  
        // Move to the next input if the current input is not empty
        if (nextInput && currentInput.value !== "") {
          nextInput.removeAttribute("disabled");
          nextInput.focus();
        }
  
        // Handle backspace key
        if (e.key === "Backspace" && prevInput) {
          inputs.forEach((input, index2) => {
            if (index1 <= index2) {
              input.setAttribute("disabled", true);
              input.value = "";
            }
          });
          prevInput.focus();
        }
  
        // Enable the button when all inputs are filled
        if (Array.from(inputs).every((input) => input.value !== "")) {
          button.classList.add("active");
          button.removeAttribute("disabled");
        } else {
          button.classList.remove("active");
          button.setAttribute("disabled", true);
        }
      });
    });
  
    // Automatically focus on the first input when the page loads
    inputs[0].removeAttribute("disabled");
    inputs[0].focus();
  });
  