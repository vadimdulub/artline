import { expect, it } from "vitest";
import { lockBodyScroll } from "../modal-scroll";

it("releases nested modal locks in either cleanup order", () => {
  for (const parentFirst of [true, false]) {
    document.body.style.overflow = "auto";
    const parent = lockBodyScroll(), child = lockBodyScroll();
    expect(document.body.style.overflow).toBe("hidden");
    (parentFirst ? parent : child)();
    expect(document.body.style.overflow).toBe("hidden");
    (parentFirst ? child : parent)();
    expect(document.body.style.overflow).toBe("auto");
    parent(); child();
    expect(document.body.style.overflow).toBe("auto");
  }
  document.body.style.overflow = "";
});
