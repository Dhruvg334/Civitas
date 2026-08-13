import { renderToStaticMarkup } from "react-dom/server";
import { expect, it } from "vitest";
import Demo from "./page";
it("renders the seeded workflow story", () => { const html = renderToStaticMarkup(<Demo />); expect(html).toContain("Seeded water-leak scenario"); expect(html).toContain("Reports"); });
