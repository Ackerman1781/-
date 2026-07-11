(function () {
  const header = document.getElementById("header");

  window.addEventListener("scroll", () => {
    if (header) {
      header.classList.toggle("scrolled", window.scrollY > 20);
    }
  }, { passive: true });

  const params = new URLSearchParams(window.location.search);
  const hasSearch = params.has("q") && params.get("q").trim() !== "";
  const hasCategory = params.has("category") && params.get("category").trim() !== "";

  if (hasSearch || hasCategory) {
    const catalog = document.getElementById("catalog");
    if (catalog) {
      requestAnimationFrame(() => {
        catalog.scrollIntoView({ behavior: "auto", block: "start" });
      });
    }
  }

  const openSheet = (el) => {
    el.classList.add("open");
    el.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  };

  const closeSheet = (el) => {
    el.classList.remove("open");
    el.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  };

  const closeAllSheets = () => {
    document.querySelectorAll(".product-sheet.open").forEach(closeSheet);
  };

  const productSheet = document.getElementById("productSheet");
  if (productSheet) {
    const photo = document.getElementById("sheetPhoto");
    const cat = document.getElementById("sheetCat");
    const title = document.getElementById("sheetTitle");
    const weight = document.getElementById("sheetWeight");
    const price = document.getElementById("sheetPrice");
    const desc = document.getElementById("sheetDesc");
    const order = document.getElementById("sheetOrder");
    const more = document.getElementById("sheetMore");

    const openProductSheet = (data) => {
      closeAllSheets();
      if (data.image) {
        photo.innerHTML = `<img src="${data.image}" alt="">`;
      } else {
        photo.innerHTML = `<div class="sheet-no-photo">🐟</div>`;
      }

      cat.textContent = data.cat || "";
      cat.style.display = data.cat ? "inline-block" : "none";
      title.textContent = data.name || "";
      weight.textContent = data.weight ? `Фасування: ${data.weight}` : "";
      weight.style.display = data.weight ? "block" : "none";
      price.textContent = data.price ? `${data.price} ₴` : "";
      desc.textContent = data.desc || "";
      desc.style.display = data.desc ? "block" : "none";
      order.href = data.order || "#";
      more.href = data.url || "#";

      openSheet(productSheet);
    };

    productSheet.querySelectorAll("[data-close-sheet]").forEach((el) => {
      el.addEventListener("click", () => closeSheet(productSheet));
    });

    document.querySelectorAll(".product-card").forEach((card) => {
      card.addEventListener("click", () => openProductSheet(card.dataset));
      card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          openProductSheet(card.dataset);
        }
      });
    });
  }

  const contactSheet = document.getElementById("contactSheet");
  const contactBtn = document.getElementById("openContactSheet");
  if (contactSheet && contactBtn) {
    contactBtn.addEventListener("click", () => {
      closeAllSheets();
      openSheet(contactSheet);
    });
    contactSheet.querySelectorAll("[data-close-contact]").forEach((el) => {
      el.addEventListener("click", () => closeSheet(contactSheet));
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeAllSheets();
  });

  const reveals = document.querySelectorAll(".reveal");
  if (!reveals.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
  );

  reveals.forEach((el) => observer.observe(el));
})();
