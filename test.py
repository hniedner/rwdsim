from datetime import date

from rwdsim.main import determine_death_date, main

if __name__ == "__main__":
    # diag_date: date = date(2020, 1, 1)
    # survival_probs: dict[int, float] = {1: 0.85, 3: 0.49, 5: 0.35, 10: 0.13}
    # runs: int = 10000
    # death_dates: list[date | None] = []
    # for _ in range(runs):
    #     death_dates.append(determine_death_date(diag_date, survival_probs))
    #
    # prob_sum = 0
    # for year in range(max(survival_probs.keys())):
    #     print(
    #         f"{diag_date.year + year}: {(count := len([d for d in death_dates if d and d.year == diag_date.year+year]))}, {count/runs}"
    #     )
    #     prob_sum += count / runs
    #
    # print(f"None: {(count := len([d for d in death_dates if not d]))}, {count/runs}")
    # prob_sum += count / runs
    # print(f"Sum: {prob_sum}")
    main()
