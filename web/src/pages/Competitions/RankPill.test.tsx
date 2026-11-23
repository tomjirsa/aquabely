import { render, screen } from "@testing-library/react";
import { RankPill } from "./RankPill";

test("filtered pill shows position and grey official half", () => {
  render(<RankPill position={1} official={3} filtered />);
  expect(screen.getByTestId("rank-position").textContent).toBe("1");
  expect(screen.getByTestId("rank-official").textContent).toBe("3");
});

test("unfiltered pill shows only the single pill", () => {
  render(<RankPill position={2} official={2} filtered={false} />);
  expect(screen.getByTestId("rank-position").textContent).toBe("2");
  expect(screen.queryByTestId("rank-official")).toBeNull();
});
