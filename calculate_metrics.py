from utils.calculate_metrics import calculate_percentage_of_fixes_and_bics_with_test_changes, calculate_the_fix_commits_with_tests_that_become_bic

calculate_percentage_of_fixes_and_bics_with_test_changes("./csv/commit_analizer.csv", "./csv/test_percentage.csv")
calculate_the_fix_commits_with_tests_that_become_bic("./json/consolidated_data.json", "./csv/commit_analizer.csv", "./csv/test_interference.csv")