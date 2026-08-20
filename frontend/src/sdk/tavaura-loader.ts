export type TavauraInitOptions = {
  tenantId: string;
  selectorOverride?: string | null;
  debug?: boolean;
  widgetBaseUrl?: string;
};

declare global {
  interface Window {
    Tavaura?: {
      init: (options: TavauraInitOptions) => void;
    };
  }
}

const DEFAULT_ADD_TO_CART_SELECTORS: string[] = [
  '[name="add"]',
  'button[name="add"]',
  'button[type="submit"][name="add"]',
  ".product-form [type=\"submit\"]",
  ".product-form button",
  ".btn-add-to-cart",
  ".add-to-cart",
  ".product__add-to-cart",
  ".single_add_to_cart_button",
];

let hasInjected = false;
let overlayEl: HTMLDivElement | null = null;

const onReady = (fn: () => void) => {
  if (typeof document === "undefined") return;
  if (document.readyState === "complete" || document.readyState === "interactive") {
    fn();
  } else {
    window.addEventListener("DOMContentLoaded", fn, { once: true });
  }
};

const findAddToCartButton = (
  opts: TavauraInitOptions
): HTMLButtonElement | HTMLInputElement | null => {
  const { selectorOverride, debug } = opts;
  const log = (...args: unknown[]) => {
    if (debug) console.debug("[Tavaura SDK]", ...args);
  };

  if (selectorOverride) {
    const el = document.querySelector(selectorOverride);
    if (el instanceof HTMLButtonElement || el instanceof HTMLInputElement) {
      log("Matched add-to-cart via selectorOverride:", selectorOverride);
      return el;
    } else {
      log("selectorOverride did not match a button/input:", selectorOverride);
    }
  }

  for (const selector of DEFAULT_ADD_TO_CART_SELECTORS) {
    const el = document.querySelector(selector);
    if (el instanceof HTMLButtonElement || el instanceof HTMLInputElement) {
      log("Matched add-to-cart via default selector:", selector);
      return el;
    }
  }

  log("No add-to-cart button found.");
  return null;
};

function injectTryOnButton(addToCart: HTMLButtonElement | HTMLInputElement, options: TavauraInitOptions) {
  const parent = addToCart.parentElement;
  if (!parent) return;

  const tryOnButton = document.createElement("button");
  tryOnButton.type = "button";
  tryOnButton.textContent = "Try on with Tavaura";
  tryOnButton.className = "tavaura-tryon-button";

  tryOnButton.style.marginLeft = "0.5rem";
  tryOnButton.style.marginTop = "0.5rem";
  tryOnButton.style.padding = "0.5rem 0.75rem";
  tryOnButton.style.borderRadius = "999px";
  tryOnButton.style.border = "1px solid rgba(31,53,60,0.45)";
  tryOnButton.style.background = "white";
  tryOnButton.style.color = "#1f353c";
  tryOnButton.style.fontSize = "0.875rem";
  tryOnButton.style.fontWeight = "500";
  tryOnButton.style.cursor = "pointer";

  tryOnButton.addEventListener("click", () => {
    if (options.debug) {
      console.debug("[Tavaura SDK] Try-on clicked for tenant:", options.tenantId);
    }
    openOverlay(options);
  });

  parent.insertBefore(tryOnButton, addToCart.nextSibling);
}

function openOverlay(options: TavauraInitOptions) {
  if (overlayEl) return;
  const baseUrl =
    options.widgetBaseUrl ||
    (typeof window !== "undefined" ? window.location.origin : "http://localhost:3000");

  const overlay = document.createElement("div");
  overlay.className = "tavaura-overlay";
  overlay.style.position = "fixed";
  overlay.style.inset = "0";
  overlay.style.zIndex = "2147483647";
  overlay.style.background = "rgba(15, 23, 42, 0.55)";
  overlay.style.display = "flex";
  overlay.style.alignItems = "center";
  overlay.style.justifyContent = "center";
  overlay.style.padding = "16px";

  const card = document.createElement("div");
  card.style.position = "relative";
  card.style.width = "100%";
  card.style.maxWidth = "960px";
  card.style.borderRadius = "24px";
  card.style.background = "rgba(255,255,255,0.97)";
  card.style.boxShadow = "0 24px 80px rgba(15,23,42,0.55)";
  card.style.overflow = "hidden";
  card.style.display = "flex";
  card.style.flexDirection = "column";
  card.style.height = "min(90vh, 720px)";

  const closeBtn = document.createElement("button");
  closeBtn.type = "button";
  closeBtn.textContent = "×";
  closeBtn.setAttribute("aria-label", "Close Tavaura");
  closeBtn.style.position = "absolute";
  closeBtn.style.top = "12px";
  closeBtn.style.right = "16px";
  closeBtn.style.width = "32px";
  closeBtn.style.height = "32px";
  closeBtn.style.borderRadius = "999px";
  closeBtn.style.border = "none";
  closeBtn.style.background = "rgba(15,23,42,0.06)";
  closeBtn.style.fontSize = "20px";
  closeBtn.style.cursor = "pointer";
  closeBtn.addEventListener("mouseenter", () => {
    closeBtn.style.background = "rgba(15,23,42,0.12)";
  });
  closeBtn.addEventListener("mouseleave", () => {
    closeBtn.style.background = "rgba(15,23,42,0.06)";
  });
  closeBtn.addEventListener("click", () => {
    if (overlayEl) {
      document.body.removeChild(overlayEl);
      overlayEl = null;
    }
  });

  const frameWrapper = document.createElement("div");
  frameWrapper.style.flex = "1";
  frameWrapper.style.padding = "16px";
  frameWrapper.style.paddingTop = "40px";
  frameWrapper.style.boxSizing = "border-box";

  const iframe = document.createElement("iframe");
  iframe.style.width = "100%";
  iframe.style.height = "100%";
  iframe.style.border = "none";
  iframe.style.borderRadius = "16px";
  iframe.setAttribute("allow", "camera; clipboard-read; clipboard-write");
  iframe.src = `${baseUrl}/sdk-demo?embed=1&tenantId=${encodeURIComponent(options.tenantId)}`;

  frameWrapper.appendChild(iframe);
  card.appendChild(closeBtn);
  card.appendChild(frameWrapper);
  overlay.appendChild(card);
  document.body.appendChild(overlay);
  overlayEl = overlay;
}

export function init(options: TavauraInitOptions) {
  if (typeof window === "undefined" || typeof document === "undefined") return;
  if (hasInjected) {
    if (options.debug) {
      console.debug("[Tavaura SDK] init called more than once; ignoring.");
    }
    return;
  }
  hasInjected = true;

  onReady(() => {
    const addToCart = findAddToCartButton(options);
    if (!addToCart) return;
    injectTryOnButton(addToCart, options);
  });
}

if (typeof window !== "undefined") {
  window.Tavaura = {
    init,
  };
}
