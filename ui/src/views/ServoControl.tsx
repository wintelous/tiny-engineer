import { useEffect, useState } from "preact/hooks";
import { sendQuietly } from "../api/client";
import { useRobot } from "../robot";
import { Button } from "../components/Button";
import { ConfigSection } from "../components/ConfigSection";
import { ServoTrack } from "../components/ServoTrack";
import { DEFAULT_SERVO_RANGES, inRange, type Range, SERVO_NAMES, savedRanges } from "../servos";
import { useStatus } from "../status/status";
import { END_CALIBRATION, ServoCalibration } from "./ServoCalibration";

// One joint selector drives both the plain move and the calibration, so the
// joint on screen is always the joint that moves.
export function ServoControl() {
  const { settings } = useRobot();
  const { perform } = useStatus();
  // Until the settings load, the stock ranges stand in.
  const ranges = settings ? savedRanges(settings) : DEFAULT_SERVO_RANGES;
  const [index, setIndex] = useState(0);
  const [angle, setAngle] = useState("90");
  // Angle of the first calibration move; null while not calibrating.
  const [calibrateFrom, setCalibrateFrom] = useState<number | null>(null);
  const calibrating = calibrateFrom !== null;
  const [min, max] = ranges[index];
  const mid = (min + max) / 2;
  const value = parseFloat(angle);
  const safe = inRange(value, ranges[index]);

  // A session left open by a closed tab or a crashed browser would keep
  // animations paused for up to two minutes; this page starts from a clean state.
  useEffect(() => {
    void sendQuietly("/servo/calibrate", END_CALIBRATION);
  }, []);

  function selectServo(next: number) {
    const [nextMin, nextMax] = ranges[next];

    setIndex(next);

    if (!inRange(value, ranges[next])) {
      setAngle(String((nextMin + nextMax) / 2));
    }
  }

  async function move(target: string) {
    await perform({
      path: "/test/servo",
      request: { method: "POST", json: { index, angle: Number(target) } },
      pending: "Moving servo…",
      failure: "Move failed",
      done: `Servo ${index} moved to ${target}°.`,
    });
  }

  async function startCalibration() {
    const start = Math.round(mid);
    const result = await perform({
      path: "/servo/calibrate",
      request: { method: "POST", json: { index, angle: start } },
      pending: "Starting calibration…",
      failure: "Calibration failed to start",
    });

    if (result?.ok) {
      setCalibrateFrom(start);
    }
  }

  function finishCalibration(saved?: Range) {
    setCalibrateFrom(null);

    // Keep the move slider inside a freshly saved range.
    if (saved && !inRange(value, saved)) {
      setAngle(String((saved[0] + saved[1]) / 2));
    }
  }

  return (
    <section>
      <h2 className="page-title">Servo control</h2>
      <p className="page-desc">Move one joint, or recalibrate its range.</p>
      <div className="form-group">
        <label htmlFor="servo-index">Joint</label>
        <select
          id="servo-index"
          value={index}
          disabled={calibrating}
          onChange={(event) => selectServo(Number(event.currentTarget.value))}
        >
          {SERVO_NAMES.map((name, servo) => (
            <option key={name} value={servo}>
              {servo} — {name}
            </option>
          ))}
        </select>
        {calibrating ? (
          <p className="hint">Save or cancel the calibration to pick another joint.</p>
        ) : (
          <p id="servo-range-hint" className={safe ? "hint" : "hint warn"}>
            {safe
              ? `Saved range: ${min}–${max}°`
              : `Outside saved range — firmware clamps to ${min}–${max}°`}
          </p>
        )}
      </div>

      {calibrating ? (
        <ServoCalibration
          index={index}
          range={ranges[index]}
          startAngle={calibrateFrom}
          onClose={finishCalibration}
        />
      ) : (
        <>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void move(angle);
            }}
          >
            <div className="form-group">
              <label htmlFor="servo-angle">Angle</label>
              <div className="range-row servo-range">
                <ServoTrack
                  background={<div className="servo-safe-band"></div>}
                  scale={[min, Math.round(mid), max]}
                >
                  <input
                    type="range"
                    className="servo-slider"
                    aria-label="Angle slider"
                    min={min}
                    max={max}
                    value={angle}
                    onInput={(event) => setAngle(event.currentTarget.value)}
                  />
                </ServoTrack>
                <input
                  type="number"
                  id="servo-angle"
                  aria-describedby="servo-range-hint"
                  required
                  min={min}
                  max={max}
                  value={angle}
                  onInput={(event) => setAngle(event.currentTarget.value)}
                />
              </div>
            </div>
            <div className="servo-actions">
              <Button
                onClick={() => {
                  setAngle(String(mid));
                  void move(String(mid));
                }}
              >
                Center
              </Button>
              <Button type="submit" variant="primary">
                Move servo
              </Button>
            </div>
          </form>
          <ConfigSection title="Calibrate range">
            <p className="config-section-desc">
              Find new min and max angles for {SERVO_NAMES[index]}. Nothing is saved until you press
              Save range.
            </p>
            <div className="servo-actions">
              <Button onClick={() => void startCalibration()}>
                Calibrate {SERVO_NAMES[index]}
              </Button>
            </div>
          </ConfigSection>
        </>
      )}
    </section>
  );
}
