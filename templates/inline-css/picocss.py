"""
PicoCSS 内联模板 — 将 PicoCSS 完整内联到 FastHTML 应用中

使用方式：
    from templates.inline_css.picocss import PICO_CSS
    app, rt = fast_app(hdrs=(Style(PICO_CSS), Script(src="htmx.js")))

获取最新版 PicoCSS：
    curl -o picocss.min.css https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css
    然后将文件内容替换到下方字符串中。
"""

PICO_CSS = """
:root {
  --pico-font-family: system-ui, -apple-system, "Segoe UI", "Roboto", sans-serif;
  --pico-line-height: 1.5;
  --pico-font-weight: 400;
  --pico-font-size: 100%;
  --pico-text-underline-offset: 0.1rem;
  --pico-border-radius: 0.25rem;
  --pico-border-width: 0.0625rem;
  --pico-outline-width: 0.125rem;
  --pico-transition: 0.2s ease-in-out;
  --pico-spacing: 1rem;
  --pico-typography-spacing-vertical: 1rem;
  --pico-block-spacing-vertical: var(--pico-spacing);
  --pico-block-spacing-horizontal: var(--pico-spacing);
  --pico-form-element-spacing-vertical: 0.5rem;
  --pico-form-element-spacing-horizontal: 0.75rem;
  --pico-group-box-shadow: 0 0 0 0.0625rem var(--pico-muted-border-color);
  --pico-group-box-shadow-focus-with-button: 0 0 0 0.0625rem var(--pico-primary-focus);
  --pico-group-box-shadow-focus-with-input: 0 0 0 0.0625rem var(--pico-primary-focus);
  --pico-background-color: #fff;
  --pico-color: #374151;
  --pico-text-selection-color: rgba(33, 99, 207, 0.25);
  --pico-muted-color: #9ca3af;
  --pico-muted-border-color: #d1d5db;
  --pico-primary: #2163cf;
  --pico-primary-background: #2163cf;
  --pico-primary-border: var(--pico-primary);
  --pico-primary-underline: rgba(33, 99, 207, 0.5);
  --pico-primary-hover: #1a4fa3;
  --pico-primary-hover-background: #1a4fa3;
  --pico-primary-hover-border: var(--pico-primary-hover);
  --pico-primary-hover-underline: rgba(26, 79, 163, 0.5);
  --pico-primary-focus: rgba(33, 99, 207, 0.25);
  --pico-color-light: #fff;
  --pico-switch-color: #fff;
  --pico-switch-background-color: #d1d5db;
  --pico-border-color: #e5e7eb;
  --pico-table-border-color: var(--pico-muted-border-color);
  --pico-table-row-stripped-background-color: rgba(33, 99, 207, 0.05);
  --pico-code-background-color: #f3f4f6;
  --pico-code-color: #374151;
  --pico-code-kbd-background-color: #374151;
  --pico-code-kbd-color: #fff;
  --pico-form-element-background-color: #f9fafb;
  --pico-form-element-selected-background-color: #e5e7eb;
  --pico-form-element-border-color: #d1d5db;
  --pico-form-element-color: #374151;
  --pico-form-element-placeholder-color: #9ca3af;
  --pico-form-element-active-background-color: #fff;
  --pico-form-element-active-border-color: var(--pico-primary);
  --pico-form-element-focus-color: var(--pico-primary);
  --pico-form-element-disabled-opacity: 0.5;
  --pico-form-element-invalid-border-color: #dc2626;
  --pico-form-element-invalid-active-border-color: #dc2626;
  --pico-form-element-invalid-focus-color: #dc2626;
  --pico-form-element-valid-border-color: #16a34a;
  --pico-form-element-valid-active-border-color: #16a34a;
  --pico-form-element-valid-focus-color: #16a34a;
  --pico-button-background-color: var(--pico-primary-background);
  --pico-button-border-color: var(--pico-primary-border);
  --pico-button-color: var(--pico-color-light);
  --pico-button-hover-background-color: var(--pico-primary-hover-background);
  --pico-button-hover-border-color: var(--pico-primary-hover-border);
  --pico-button-hover-color: var(--pico-color-light);
  --pico-button-focus: var(--pico-primary-focus);
  --pico-button-secondary-background-color: #9ca3af;
  --pico-button-secondary-border-color: #9ca3af;
  --pico-button-secondary-hover-background-color: #6b7280;
  --pico-button-secondary-hover-border-color: #6b7280;
  --pico-button-contrast-background-color: #374151;
  --pico-button-contrast-border-color: #374151;
}

/* Light color scheme (prefers-color-scheme) */
@media (prefers-color-scheme: light) {
  :root:not([data-theme=dark]) {
    --pico-background-color: #fff;
    --pico-color: #374151;
  }
}

/* Body */
body {
  margin: 0;
  font-family: var(--pico-font-family);
  line-height: var(--pico-line-height);
  font-weight: var(--pico-font-weight);
  font-size: var(--pico-font-size);
  background-color: var(--pico-background-color);
  color: var(--pico-color);
  -webkit-text-size-adjust: 100%;
  -webkit-tap-highlight-color: transparent;
}

/* Container */
.container, main {
  width: 100%;
  margin-right: auto;
  margin-left: auto;
  padding-right: var(--pico-spacing);
  padding-left: var(--pico-spacing);
  max-width: 960px;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
  --pico-font-weight: 600;
  --pico-line-height: 1.25;
  margin-top: 0;
  margin-bottom: var(--pico-typography-spacing-vertical);
  color: var(--pico-color);
}

h1 { font-size: 2rem; }
h2 { font-size: 1.5rem; }
h3 { font-size: 1.25rem; }

/* Links */
a {
  color: var(--pico-primary);
  text-decoration: underline;
  text-underline-offset: var(--pico-text-underline-offset);
}
a:hover { color: var(--pico-primary-hover); }

/* Buttons */
button, [type=submit], [type=button], [type=reset] {
  display: inline-block;
  padding: var(--pico-form-element-spacing-vertical) var(--pico-form-element-spacing-horizontal);
  font-family: inherit;
  font-size: inherit;
  font-weight: 500;
  line-height: 1.25;
  text-align: center;
  text-decoration: none;
  cursor: pointer;
  border: var(--pico-border-width) solid var(--pico-button-border-color);
  border-radius: var(--pico-border-radius);
  background-color: var(--pico-button-background-color);
  color: var(--pico-button-color);
  transition: background-color var(--pico-transition), border-color var(--pico-transition), color var(--pico-transition);
}
button:hover { background-color: var(--pico-button-hover-background-color); border-color: var(--pico-button-hover-border-color); color: var(--pico-button-hover-color); }
button.secondary { --pico-button-background-color: var(--pico-button-secondary-background-color); --pico-button-border-color: var(--pico-button-secondary-border-color); }
button.secondary:hover { --pico-button-background-color: var(--pico-button-secondary-hover-background-color); --pico-button-border-color: var(--pico-button-secondary-hover-border-color); }
button.small { font-size: 0.85rem; padding: 0.3rem 0.5rem; }
button:disabled { opacity: 0.5; cursor: not-allowed; }

/* Form elements */
input, select, textarea, label {
  display: block;
  margin-bottom: 0.25rem;
  font-family: inherit;
  font-size: inherit;
}
input, select, textarea {
  width: 100%;
  padding: var(--pico-form-element-spacing-vertical) var(--pico-form-element-spacing-horizontal);
  border: var(--pico-border-width) solid var(--pico-form-element-border-color);
  border-radius: var(--pico-border-radius);
  background-color: var(--pico-form-element-background-color);
  color: var(--pico-form-element-color);
  transition: background-color var(--pico-transition), border-color var(--pico-transition);
}
input:hover, select:hover, textarea:hover { border-color: var(--pico-primary-hover); }
input:active, select:active, textarea:active { background-color: var(--pico-form-element-active-background-color); }
input:focus, select:focus, textarea:focus { border-color: var(--pico-form-element-active-border-color); outline: none; box-shadow: 0 0 0 var(--pico-outline-width) var(--pico-form-element-focus-color); }

/* Tables */
table { width: 100%; border-collapse: collapse; margin-bottom: var(--pico-block-spacing-vertical); }
th, td { padding: 0.5rem; text-align: left; border-bottom: var(--pico-border-width) solid var(--pico-table-border-color); }
th { font-weight: 600; }
tbody tr:nth-child(even) { background-color: var(--pico-table-row-stripped-background-color); }

/* Utilities */
.small { font-size: 0.85rem; color: var(--pico-muted-color); }
"""
