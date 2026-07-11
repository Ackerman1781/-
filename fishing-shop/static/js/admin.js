(function () {
  const toggle = document.getElementById("menuToggle");
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("adminOverlay");

  function closeMenu() {
    sidebar?.classList.remove("open");
    overlay?.classList.remove("open");
    document.body.style.overflow = "";
  }

  function openMenu() {
    sidebar?.classList.add("open");
    overlay?.classList.add("open");
    document.body.style.overflow = "hidden";
  }

  toggle?.addEventListener("click", () => {
    if (sidebar?.classList.contains("open")) closeMenu();
    else openMenu();
  });

  overlay?.addEventListener("click", closeMenu);
})();
