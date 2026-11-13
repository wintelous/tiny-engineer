import { useEffect, useRef, useState } from "preact/hooks";
import { sendQuietly, type Request } from "../api/client";
import type { Settings } from "../api/types";
import { Button } from "../components/Button";
import { ConfigSection } from "../components/ConfigSection";
import { useRobot } from "../robot";
import { SERVO_NAMES, type Range } from "../servos";
import { useStatus } from "../status/status";

const NUDGES = [-5, -1, 1, 5] as const;
const ANGLE_MIN = 0;
const ANGLE_MAX = 180;

export const END_CALIBRATION: Request = { method: "POST", json: { end: true } };

const clampAngle = (angle: number) => Math.min(ANGLE_MAX, Math.max(ANGLE_MIN, angle));

// Calibration of the joint picked on the Servo page. The robot holds a session
// while this panel is open: animations pause and the joint may pass its saved
// limits. Only Save range writes anything. Cancel, leaving the page or closing
// the tab ends the session and the saved range stays in force.
export function ServoCalibration({
  index,
  range: [savedMin, savedMax],
  startAngle,
  onClose,
}: {
  index: number;
  range: Range;
  startAngle: number;
  // Called with the new range after a save, without one after a cancel.
  onClose: (saved?: Range) => void;
}) {
  const { applySettings } = useRobot();
  const { perform } = useStatus();
  const [angle, setAngle] = useState(startAngle);
  const [draftMin, setDraftMin] = useState<number | null>(null);
  const [draftMax, setDraftMax] = useState<number | null>(null);
  // False once Save or Cancel has closed the session on the robot.
  const openRef = useRef(true);
  const newMin = draftMin ?? savedMin;
  const newMax = draftMax ?? savedMax;
  const rangeOk = newMin < newMax;
  const changed = newMin !== savedMin || newMax !== savedMax;
  const name = SERVO_NAMES[index];

  // Leaving the page (another page of the UI, reload, closed tab) abandons the
  // calibration: end the session so animations run on the saved range again.
  useEffect(() => {
    const abandon = () => {
      if (openRef.current) {
        openRef.current = false;
        void sendQuietly("/servo/calibrate", { ...END_CALIBRATION, keepalive: true });
      }
    };

    window.addEventListener("pagehide", abandon);

    return () => {
      window.removeEventListener("pagehide", abandon);
      abandon();
    };
  }, []);

  async function moveTo(target: number) {
    const next = clampAngle(Math.round(target));
    const result = await perform({
      path: "/servo/calibrate",
      request: { method: "POST", json: { index, angle: next } },
      pending: "Moving…",
      failure: "Calibration move failed",
    });

    if (result?.ok) {
      setAngle(next);
    }
  }

  async function cancel() {
    const result = await perform({
      path: "/servo/calibrate",
      request: END_CALIBRATION,
      pending: "Cancelling…",
      failure: "Cancel failed",
      done: `Calibration cancelled; ${name} keeps ${savedMin}–${savedMax}°.`,
    });

    if (result?.ok) {
      openRef.current = false;
      onClose();
    }
  }

  async function save() {
    await perform<Settings>({
      path: "/settings/servo",
      request: { method: "PUT", json: { index, min: newMin, max: newMax } },
      pending: "Saving range…",
      failure: "Save failed",
      done: `${name} range saved: ${newMin}–${newMax}°.`,
      onSuccess: (saved) => {
        // Saving closes the session on the robot.
        openRef.current = false;
        applySettings(saved);
        onClose([newMin, newMax]);
      },
    });
  }

  return (
    <ConfigSection title={`Calibrating ${index} — ${name}`}>
      <p className="config-section-desc">
        The joint moves slowly and can go past its saved limits: nudge in small steps and stop
        before a part binds or a cable pulls taut.
      </p>
      <p className="config-section-desc">
        Nothing is saved until you press Save range. Cancel, or leaving this page, keeps the saved
        range. Animations and agent hooks pause until then.
      </p>

      <div className="form-group">
        <div className="field-head">
          <span>Current angle: {angle}°</span>
        </div>
        <div className="calib-nudges" role="group" aria-label="Nudge joint">
          {NUDGES.map((step) => (
            <Button
              key={step}
              aria-label={`Nudge ${step > 0 ? "+" : ""}${step}°`}
              disabled={angle + step < ANGLE_MIN || angle + step > ANGLE_MAX}
              onClick={() => void moveTo(angle + step)}
            >
              {step > 0 ? `+${step}` : step}°
            </Button>
          ))}
        </div>
      </div>
      <div className="servo-actions">
        <Button onClick={() => setDraftMin(angle)}>Set as min</Button>
        <Button onClick={() => setDraftMax(angle)}>Set as max</Button>
        <Button onClick={() => void moveTo(newMin)}>Go to min</Button>
        <Button onClick={() => void moveTo(newMax)}>Go to max</Button>
      </div>

      <p className="hint">
        Saved range: {savedMin}–{savedMax}°
      </p>
      <p className={rangeOk ? "hint" : "hint warn"}>
        {rangeOk
          ? `New range: ${newMin}–${newMax}°${changed ? "" : " (unchanged)"}`
          : `Min (${newMin}°) must be below max (${newMax}°)`}
      </p>

      <div className="servo-actions">
        <Button onClick={() => void cancel()}>Cancel</Button>
        <Button variant="primary" disabled={!rangeOk || !changed} onClick={() => void save()}>
          Save range
        </Button>
      </div>
    </ConfigSection>
  );
}
