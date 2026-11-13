import { screen, waitFor } from "@testing-library/preact";
import { describe, expect, it } from "vitest";
import { fakeRobot, renderApp } from "./robot";

async function typeAngle(user: ReturnType<typeof renderApp>["user"], value: string) {
  const angle = await screen.findByRole("spinbutton", { name: "Angle" });

  await user.clear(angle);
  await user.type(angle, value);
}

describe("servo page", () => {
  it("bounds the slider by the selected joint's saved range", async () => {
    fakeRobot({
      settings: { servo_mins: [70, 40, 45, 35, 40], servo_maxs: [110, 130, 135, 125, 130] },
    });
    renderApp("/servo");

    const slider = await screen.findByLabelText("Angle slider");

    await waitFor(() => expect(slider.getAttribute("min")).toBe("70"));
    expect(slider.getAttribute("max")).toBe("110");
  });

  it("warns when a typed angle is outside the safe range", async () => {
    fakeRobot();
    const { user } = renderApp("/servo");

    await typeAngle(user, "150");

    expect(screen.getByText(/firmware clamps to 80–100°/).classList.contains("warn")).toBe(true);
  });

  it("moves only when the form is submitted", async () => {
    const robot = fakeRobot();
    const { user, click } = renderApp("/servo");

    await typeAngle(user, "100");

    expect(robot.sent("POST", "/test/servo")).toHaveLength(0);

    await click("Move servo");

    await waitFor(() =>
      expect(robot.lastPost("/test/servo")?.json).toEqual({ index: 0, angle: 100 }),
    );
  });

  it("has one joint selector for moving and calibrating", async () => {
    fakeRobot();
    renderApp("/servo");

    await screen.findByLabelText("Joint");

    expect(screen.getAllByRole("combobox")).toHaveLength(1);
  });

  it("calibrates the selected joint and saves only its range", async () => {
    const robot = fakeRobot({
      settings: { servo_mins: [70, 65, 80, 76, 54], servo_maxs: [140, 153, 147, 145, 148] },
    });
    const { user, click } = renderApp("/servo");

    await user.selectOptions(await screen.findByLabelText("Joint"), "2");
    await click("Calibrate Left hand");

    await waitFor(() =>
      expect(robot.lastPost("/servo/calibrate")?.json).toEqual({ index: 2, angle: 114 }),
    );
    expect(screen.getByLabelText<HTMLSelectElement>("Joint").disabled).toBe(true);
    expect(screen.queryByRole("button", { name: "Move servo" })).toBeNull();

    await click("Nudge -5°");
    await click("Nudge -1°");
    await waitFor(() =>
      expect(robot.lastPost("/servo/calibrate")?.json).toEqual({ index: 2, angle: 108 }),
    );
    await click("Set as min");
    await click("Nudge +5°");
    await click("Set as max");

    expect(screen.getByText("New range: 108–113°")).toBeTruthy();
    expect(robot.sent("PUT", "/settings/servo")).toHaveLength(0);

    await click("Save range");

    await waitFor(() =>
      expect(robot.sent("PUT", "/settings/servo").at(-1)?.json).toEqual({
        index: 2,
        min: 108,
        max: 113,
      }),
    );
    expect(await screen.findByText("Saved range: 108–113°")).toBeTruthy();
    expect(screen.getByLabelText<HTMLSelectElement>("Joint").disabled).toBe(false);
    expect(screen.getByRole("button", { name: "Calibrate Left hand" })).toBeTruthy();
  });

  it("blocks saving when min is not below max", async () => {
    fakeRobot();
    const { click } = renderApp("/servo");

    await click("Calibrate Head");
    await click("Set as max");
    await click("Nudge +1°");
    await click("Set as min");

    expect(screen.getByText("Min (91°) must be below max (90°)").classList.contains("warn")).toBe(
      true,
    );
    expect(screen.getByRole<HTMLButtonElement>("button", { name: "Save range" }).disabled).toBe(
      true,
    );
  });

  it("does not offer to save an unchanged range", async () => {
    fakeRobot();
    const { click } = renderApp("/servo");

    await click("Calibrate Head");

    expect(await screen.findByText("New range: 80–100° (unchanged)")).toBeTruthy();
    expect(screen.getByRole<HTMLButtonElement>("button", { name: "Save range" }).disabled).toBe(
      true,
    );
  });

  it("cancel ends the session without saving", async () => {
    const robot = fakeRobot();
    const { click } = renderApp("/servo");

    await click("Calibrate Head");
    await click("Set as min");
    await click("Cancel");

    await waitFor(() => expect(robot.lastPost("/servo/calibrate")?.json).toEqual({ end: true }));
    expect(robot.sent("PUT", "/settings/servo")).toHaveLength(0);
    expect(screen.getByLabelText<HTMLSelectElement>("Joint").disabled).toBe(false);
  });

  it("leaving the page ends the session without saving", async () => {
    const robot = fakeRobot();
    const { user, click } = renderApp("/servo");

    await click("Calibrate Head");
    await click("Nudge +5°");
    const ends = robot.sent("POST", "/servo/calibrate").length;

    await user.click(screen.getByRole("link", { name: "Animations" }));

    await waitFor(() => expect(robot.sent("POST", "/servo/calibrate")).toHaveLength(ends + 1));
    expect(robot.lastPost("/servo/calibrate")?.json).toEqual({ end: true });
    expect(robot.sent("PUT", "/settings/servo")).toHaveLength(0);
  });

  it("ends a session left open when the page opens", async () => {
    const robot = fakeRobot();

    renderApp("/servo");

    await waitFor(() =>
      expect(robot.sent("POST", "/servo/calibrate").at(0)?.json).toEqual({ end: true }),
    );
  });
});
