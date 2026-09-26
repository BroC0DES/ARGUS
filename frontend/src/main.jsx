import React from "react";
import { createRoot } from "react-dom/client";
import { createIcons, icons } from "lucide";
import "./styles/styles.css";
import "./app.css";
import ConsoleApp from "./ConsoleApp.jsx";

// The ARGUS design-system bundle is a pre-compiled script that expects React and
// Lucide as globals. Set them, then load it before mounting.
window.React = React;
window.lucide = { createIcons: (opts) => createIcons({ icons, ...opts }) };

const script = document.createElement("script");
script.src = `${import.meta.env.BASE_URL}ds_bundle.js`;
script.onload = () => createRoot(document.getElementById("root")).render(<ConsoleApp />);
script.onerror = () => {
  document.getElementById("root").textContent = "Failed to load the ARGUS design system bundle (ds_bundle.js).";
};
document.head.appendChild(script);
