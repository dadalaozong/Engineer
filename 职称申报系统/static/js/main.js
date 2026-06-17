// Modal helpers
function openModal(id) {
  document.getElementById(id).classList.remove("hidden");
}
function closeModal(id) {
  document.getElementById(id).classList.add("hidden");
}

// Close modal on overlay click
document.addEventListener("click", function(e) {
  if (e.target.classList.contains("modal-overlay")) {
    e.target.classList.add("hidden");
  }
});

// Confirm + POST delete
function confirmDelete(url, name) {
  if (!confirm(`确认删除「${name}」？此操作不可撤销。`)) return;
  const form = document.createElement("form");
  form.method = "post";
  form.action = url;
  document.body.appendChild(form);
  form.submit();
}

// Auto-dismiss flash messages
document.addEventListener("DOMContentLoaded", function() {
  document.querySelectorAll(".alert").forEach(el => {
    setTimeout(() => {
      el.style.transition = "opacity 0.5s";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 500);
    }, 4000);
  });
});
