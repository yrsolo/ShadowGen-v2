"use client";

interface AngleSliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  valueLabel?: string;
  onChange: (value: number) => void;
}

export function AngleSlider({ label, value, min, max, valueLabel, onChange }: AngleSliderProps) {
  return (
    <section className="stack">
      <div className="slider-readout">
        <span>{label}</span>
        <strong>{valueLabel ?? String(value)}</strong>
      </div>
      <input
        className="slider"
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </section>
  );
}
