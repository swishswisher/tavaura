export type TavauraInitOptions = {
  tenantId?: string;
  theme?: "light" | "dark";
  mode?: "avatar" | "photo";
};

export function initTavaura(
  selector: string,
  options: TavauraInitOptions = {}
): void {
  const host = document.querySelector<HTMLElement>(selector);

  if (!host) {
    console.warn("Tavaura: host element not found for selector", selector);
    return;
  }

  console.log("Tavaura SDK demo initialized", options);

  host.innerHTML = "";

  const container = document.createElement("div");
  container.style.background = "white";
  container.style.border = "1px solid rgba(0,0,0,0.08)";
  container.style.borderRadius = "16px";
  container.style.padding = "16px";
  container.style.maxWidth = "320px";
  container.style.boxShadow = "0 10px 30px rgba(0,0,0,0.08)";
  container.style.fontFamily = "Inter, system-ui, -apple-system, sans-serif";
  container.style.color = "#1f353c";

  const button = document.createElement("button");
  button.textContent = "Try on with Tavaura";
  button.style.cursor = "pointer";
  button.style.display = "inline-flex";
  button.style.alignItems = "center";
  button.style.justifyContent = "center";
  button.style.padding = "10px 14px";
  button.style.borderRadius = "9999px";
  button.style.border = "1px solid rgba(31,53,60,0.18)";
  button.style.background = "#1f353c";
  button.style.color = "white";
  button.style.fontWeight = "600";
  button.style.fontSize = "14px";
  button.style.boxShadow = "0 8px 20px rgba(31,53,60,0.18)";

  const panel = document.createElement("div");
  panel.style.display = "none";
  panel.style.marginTop = "12px";
  panel.style.padding = "12px";
  panel.style.borderRadius = "12px";
  panel.style.border = "1px solid rgba(0,0,0,0.06)";
  panel.style.background = "#f8fafb";

  const title = document.createElement("div");
  title.textContent = "Tavaura demo viewer";
  title.style.fontWeight = "600";
  title.style.marginBottom = "6px";

  const body = document.createElement("p");
  body.textContent =
    "In the full product, this is where shoppers will try outfits on avatars or photos.";
  body.style.margin = "0";
  body.style.fontSize = "14px";
  body.style.lineHeight = "1.5";

  panel.appendChild(title);
  panel.appendChild(body);

  button.addEventListener("click", () => {
    panel.style.display = panel.style.display === "none" ? "block" : "none";
  });

  container.appendChild(button);
  container.appendChild(panel);

  host.appendChild(container);
}
