import { render } from "@testing-library/react";
import { ClubAverageLine } from "./ClubAverageLine";
import { JudgeBarChart } from "./JudgeBarChart";
import { PositionsChart } from "./PositionsChart";
import { ScoreLine } from "./ScoreLine";

test("charts render with empty arrays without throwing", () => {
  expect(() => {
    render(<ScoreLine rows={[]} />);
    render(<PositionsChart ranks={[]} figures={[]} />);
    render(<JudgeBarChart points={[]} />);
  }).not.toThrow();
});

test("ClubAverageLine renders with an empty array without throwing", () => {
  expect(() => render(<ClubAverageLine rows={[]} />)).not.toThrow();
});
