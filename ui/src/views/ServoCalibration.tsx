import { useState } from "preact/hooks";
import type { Settings } from "../api/types";
import { Button } from "../components/Button";
import { ConfigSection } from "../components/ConfigSection";
import { useRobot } from "../robot";
import { DEFAULT_SERVO_RANGES, SERVO_NAMES, savedRanges } from "../servos";
import { useStatus } from "../status/status";

const NUDGES = [-5, -1, 1, 5] as const;
const ANGLE_MIN = 0;
const ANGLE_MAX = 180;

const clampAngle = (angle: number) => Math.min(ANGLE_MAX, Math.max(ANGLE_MIN, angle));

// Recalibrate one joint outside setup mode. The robot pauses animations while a
// session is open and closes it on save, on cancel, or after two quiet minutes.
export function ServoCalibration() {
  const { settings, applySettings } = useRobot();
  const { perform } = useStatus();
  const ranges = settings ? savedRanges(settings) : DEFAULT_SERVO_RANGES;
  const [index, setIndex] = useState(0);
  const [active, setActive] = useState(false);
  const [angle, setAngle] = useState(0);
  const [draftMin, setDraftMin] = useState<number | null>(null);
  const [draftMax, setDraftMax] = useState<number | null>(null);
  const [savedMin, savedMax] = ranges[index];
  const newMin = draftMin ?? savedMin;
  const newMax = draftMax ?? savedMax;
  const rangeOk = newMin < newMax;

  async function moveTo(target: number) {
    const next = clampAngle(Math.round(target));
    const result = await perform({
      path: "/servo/calibrate",
      request: { method: "POST", json: { index, angle: next } },
      pending: "Moving…",
      failure: "Calibration move failed",
    });

    if (result?.ok) {
      setActive(true);
      setAngle(next);
    }
  }

  function reset() {
    setActive(false);
    setDraftMin(null);
    setDraftMax(null);
  }

  async function cancel() {
    const result = await perform({
      path: "/servo/calibrate",
      request: { method: "POST", json: { end: true } },
      pending: "Ending calibration…",
      failure: "Cancel failed",
      done: "Calibration cancelled; saved range kept.",
    });

    if (result?.ok) {
      reset();
    }
  }

  async function save() {
    await perform<Settings>({
      path: "/settings/servo",
      request: { method: "PUT", json: { index, min: newMin, max: newMax } },
      pending: "Saving range…",
      failure: "Save failed",
      done: `${SERVO_NAMES[index]} range saved: ${newMin}–${newMax}°.`,
      onSuccess: (saved) => {
        applySettings(saved);
        reset();
      },
    });
  }

  return (
    <ConfigSection title="Calibrate one joint" apply="now">
      <p className="config-section-desc">
        Moves slowly and may go past the saved limits. Nudge in small steps and stop before a part
        binds or a cable pulls taut. Animations pause until you save or cancel.
      </p>
      <div className="form-group">
        <label htmlFor="calib-index">Joint</label>
        <select
          id="calib-index"
          value={index}
          disabled={active}
          onChange={(event) => {
            setIndex(Number(event.currentTarget.value));
            setDraftMin(null);
            setDraftMax(null);
          }}
        >
          {SERVO_NAMES.map((name, servo) => (
            <option key={name} value={servo}>
              {servo} — {name}
            </option>
          ))}
        </select>
        <p className="hint">
          Saved range: {savedMin}–{savedMax}°
        </p>
      </div>

      {active ? (
        <>
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
          <p className={rangeOk ? "hint" : "hint warn"}>
            {rangeOk
              ? `New range: ${newMin}–${newMax}°`
              : `Min (${newMin}°) must be below max (${newMax}°)`}
          </p>
          <div className="servo-actions">
            <Button onClick={() => void cancel()}>Cancel</Button>
            <Button variant="primary" disabled={!rangeOk} onClick={() => void save()}>
              Save range
            </Button>
          </div>
        </>
      ) : (
        <div className="servo-actions">
          <Button variant="primary" onClick={() => void moveTo((savedMin + savedMax) / 2)}>
            Start calibration
          </Button>
        </div>
      )}
    </ConfigSection>
  );
}
