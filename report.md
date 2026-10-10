# Network-1 Ablation Study

## Experimental design

- Allocation methods: A1 MFG only, A2 Stackelberg only,
  A3 MFG + Stackelberg, and Proposed priority-aware MFG + Stackelberg.
- Load levels: 1250, 2500, 5000.
- Priority profiles: T1, T2, T3.
- Replication labels: 11, 22, 33, 44, 55.
- Total runs: 180.
- Matched conditions: load, priority profile, and replication seed.
- Each method uses the same generated workload and a fresh environment
  initialized with the same seed within each matched condition.
- Resource feasibility filtering is shared across all methods.

## Overall results

Values are means and sample standard deviations across the experiment runs.
These overall figures are descriptive and combine different loads and profiles.

| policy_variant | utility_mean_mean | utility_mean_sd | jain_fairness_mean | jain_fairness_sd | load_variance_mean | load_variance_sd | allocation_time_seconds_mean | allocation_time_seconds_sd | throughput_mean | throughput_sd | response_time_mean_mean | response_time_mean_sd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1_MFG_ONLY | 0.62776 | 0.00417 | 0.95285 | 0.00649 | 0.00154 | 0.00036 | 0.00022 | 0.00002 | 0.26213 | 0.00817 | 28.71485 | 0.20300 |
| A2_STACKELBERG_ONLY | 0.62853 | 0.00430 | 0.94802 | 0.01002 | 0.00161 | 0.00044 | 0.00008 | 0.00001 | 0.25989 | 0.00738 | 28.62700 | 0.25754 |
| A3_MFG_STACKELBERG | 0.62791 | 0.00410 | 0.94960 | 0.00836 | 0.00161 | 0.00032 | 0.00032 | 0.00003 | 0.26165 | 0.00843 | 28.70552 | 0.18751 |
| PROPOSED | 0.62980 | 0.00399 | 0.95134 | 0.01024 | 0.00151 | 0.00026 | 0.00032 | 0.00003 | 0.26164 | 0.00762 | 28.65725 | 0.18926 |

## Results by load and priority profile

Values are mean ± sample standard deviation across replications.

| load | profile_id | policy_variant | replication_count | utility_mean | jain_fairness | load_variance | allocation_time_seconds | throughput | response_time_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1250 | T1 | A1_MFG_ONLY | 5 | 0.62977 ± 0.00500 | 0.95566 ± 0.00748 | 0.00155 ± 0.00030 | 0.00022 ± 0.00002 | 0.25872 ± 0.00769 | 28.63259 ± 0.13428 |
| 1250 | T1 | A2_STACKELBERG_ONLY | 5 | 0.63049 ± 0.00664 | 0.94903 ± 0.00892 | 0.00136 ± 0.00017 | 0.00009 ± 0.00002 | 0.25648 ± 0.00752 | 28.48244 ± 0.30221 |
| 1250 | T1 | A3_MFG_STACKELBERG | 5 | 0.62865 ± 0.00458 | 0.94401 ± 0.00725 | 0.00159 ± 0.00018 | 0.00032 ± 0.00002 | 0.25952 ± 0.00863 | 28.63311 ± 0.08910 |
| 1250 | T1 | PROPOSED | 5 | 0.63006 ± 0.00506 | 0.95142 ± 0.01430 | 0.00149 ± 0.00030 | 0.00032 ± 0.00001 | 0.25872 ± 0.00378 | 28.67159 ± 0.20482 |
| 1250 | T2 | A1_MFG_ONLY | 5 | 0.62840 ± 0.00447 | 0.95566 ± 0.00748 | 0.00155 ± 0.00030 | 0.00022 ± 0.00000 | 0.25872 ± 0.00769 | 28.63259 ± 0.13428 |
| 1250 | T2 | A2_STACKELBERG_ONLY | 5 | 0.62934 ± 0.00622 | 0.94903 ± 0.00892 | 0.00136 ± 0.00017 | 0.00008 ± 0.00001 | 0.25648 ± 0.00752 | 28.48244 ± 0.30221 |
| 1250 | T2 | A3_MFG_STACKELBERG | 5 | 0.62764 ± 0.00480 | 0.94401 ± 0.00725 | 0.00159 ± 0.00018 | 0.00031 ± 0.00001 | 0.25952 ± 0.00863 | 28.63311 ± 0.08910 |
| 1250 | T2 | PROPOSED | 5 | 0.62909 ± 0.00451 | 0.94517 ± 0.00751 | 0.00151 ± 0.00014 | 0.00032 ± 0.00003 | 0.26080 ± 0.00709 | 28.53813 ± 0.20228 |
| 1250 | T3 | A1_MFG_ONLY | 5 | 0.62754 ± 0.00444 | 0.95566 ± 0.00748 | 0.00155 ± 0.00030 | 0.00022 ± 0.00001 | 0.25872 ± 0.00769 | 28.63259 ± 0.13428 |
| 1250 | T3 | A2_STACKELBERG_ONLY | 5 | 0.62854 ± 0.00619 | 0.94903 ± 0.00892 | 0.00136 ± 0.00017 | 0.00008 ± 0.00000 | 0.25648 ± 0.00752 | 28.48244 ± 0.30221 |
| 1250 | T3 | A3_MFG_STACKELBERG | 5 | 0.62670 ± 0.00427 | 0.94401 ± 0.00725 | 0.00159 ± 0.00018 | 0.00031 ± 0.00002 | 0.25952 ± 0.00863 | 28.63311 ± 0.08910 |
| 1250 | T3 | PROPOSED | 5 | 0.62874 ± 0.00541 | 0.95212 ± 0.00462 | 0.00145 ± 0.00019 | 0.00034 ± 0.00004 | 0.26048 ± 0.00472 | 28.59408 ± 0.22678 |
| 2500 | T1 | A1_MFG_ONLY | 5 | 0.62901 ± 0.00451 | 0.95262 ± 0.00522 | 0.00160 ± 0.00031 | 0.00022 ± 0.00001 | 0.26784 ± 0.00668 | 28.79322 ± 0.32538 |
| 2500 | T1 | A2_STACKELBERG_ONLY | 5 | 0.63112 ± 0.00351 | 0.94628 ± 0.01226 | 0.00183 ± 0.00034 | 0.00008 ± 0.00000 | 0.26352 ± 0.00730 | 28.59274 ± 0.28232 |
| 2500 | T1 | A3_MFG_STACKELBERG | 5 | 0.63062 ± 0.00557 | 0.95071 ± 0.00934 | 0.00147 ± 0.00038 | 0.00031 ± 0.00001 | 0.26608 ± 0.00979 | 28.71617 ± 0.25033 |
| 2500 | T1 | PROPOSED | 5 | 0.63207 ± 0.00429 | 0.95335 ± 0.00803 | 0.00163 ± 0.00034 | 0.00030 ± 0.00000 | 0.26672 ± 0.01226 | 28.59024 ± 0.16271 |
| 2500 | T2 | A1_MFG_ONLY | 5 | 0.62769 ± 0.00469 | 0.95262 ± 0.00522 | 0.00160 ± 0.00031 | 0.00022 ± 0.00001 | 0.26784 ± 0.00668 | 28.79322 ± 0.32538 |
| 2500 | T2 | A2_STACKELBERG_ONLY | 5 | 0.62972 ± 0.00395 | 0.94628 ± 0.01226 | 0.00183 ± 0.00034 | 0.00008 ± 0.00000 | 0.26352 ± 0.00730 | 28.59274 ± 0.28232 |
| 2500 | T2 | A3_MFG_STACKELBERG | 5 | 0.62921 ± 0.00570 | 0.95071 ± 0.00934 | 0.00147 ± 0.00038 | 0.00034 ± 0.00003 | 0.26608 ± 0.00979 | 28.71617 ± 0.25033 |
| 2500 | T2 | PROPOSED | 5 | 0.63203 ± 0.00477 | 0.94892 ± 0.00603 | 0.00140 ± 0.00022 | 0.00032 ± 0.00003 | 0.26272 ± 0.00777 | 28.63163 ± 0.18123 |
| 2500 | T3 | A1_MFG_ONLY | 5 | 0.62651 ± 0.00418 | 0.95262 ± 0.00522 | 0.00160 ± 0.00031 | 0.00026 ± 0.00004 | 0.26784 ± 0.00668 | 28.79322 ± 0.32538 |
| 2500 | T3 | A2_STACKELBERG_ONLY | 5 | 0.62864 ± 0.00349 | 0.94628 ± 0.01226 | 0.00183 ± 0.00034 | 0.00009 ± 0.00001 | 0.26352 ± 0.00730 | 28.59274 ± 0.28232 |
| 2500 | T3 | A3_MFG_STACKELBERG | 5 | 0.62802 ± 0.00529 | 0.95071 ± 0.00934 | 0.00147 ± 0.00038 | 0.00038 ± 0.00003 | 0.26608 ± 0.00979 | 28.71617 ± 0.25033 |
| 2500 | T3 | PROPOSED | 5 | 0.63110 ± 0.00417 | 0.95016 ± 0.01319 | 0.00147 ± 0.00024 | 0.00037 ± 0.00005 | 0.26448 ± 0.00498 | 28.49145 ± 0.07209 |
| 5000 | T1 | A1_MFG_ONLY | 5 | 0.62796 ± 0.00401 | 0.95026 ± 0.00728 | 0.00147 ± 0.00053 | 0.00022 ± 0.00002 | 0.25984 ± 0.00890 | 28.71873 ± 0.10512 |
| 5000 | T1 | A2_STACKELBERG_ONLY | 5 | 0.62743 ± 0.00105 | 0.94874 ± 0.01151 | 0.00163 ± 0.00064 | 0.00008 ± 0.00000 | 0.25968 ± 0.00769 | 28.80583 ± 0.06780 |
| 5000 | T1 | A3_MFG_STACKELBERG | 5 | 0.62776 ± 0.00165 | 0.95409 ± 0.00710 | 0.00178 ± 0.00039 | 0.00032 ± 0.00002 | 0.25936 ± 0.00730 | 28.76729 ± 0.21644 |
| 5000 | T1 | PROPOSED | 5 | 0.62901 ± 0.00207 | 0.95094 ± 0.00732 | 0.00148 ± 0.00019 | 0.00031 ± 0.00002 | 0.26112 ± 0.00785 | 28.74386 ± 0.07108 |
| 5000 | T2 | A1_MFG_ONLY | 5 | 0.62706 ± 0.00431 | 0.95026 ± 0.00728 | 0.00147 ± 0.00053 | 0.00020 ± 0.00001 | 0.25984 ± 0.00890 | 28.71873 ± 0.10512 |
| 5000 | T2 | A2_STACKELBERG_ONLY | 5 | 0.62627 ± 0.00152 | 0.94874 ± 0.01151 | 0.00163 ± 0.00064 | 0.00008 ± 0.00000 | 0.25968 ± 0.00769 | 28.80583 ± 0.06780 |
| 5000 | T2 | A3_MFG_STACKELBERG | 5 | 0.62680 ± 0.00224 | 0.95409 ± 0.00710 | 0.00178 ± 0.00039 | 0.00030 ± 0.00002 | 0.25936 ± 0.00730 | 28.76729 ± 0.21644 |
| 5000 | T2 | PROPOSED | 5 | 0.62851 ± 0.00209 | 0.95901 ± 0.01809 | 0.00148 ± 0.00030 | 0.00030 ± 0.00002 | 0.26032 ± 0.01019 | 28.87515 ± 0.10009 |
| 5000 | T3 | A1_MFG_ONLY | 5 | 0.62587 ± 0.00416 | 0.95026 ± 0.00728 | 0.00147 ± 0.00053 | 0.00021 ± 0.00001 | 0.25984 ± 0.00890 | 28.71873 ± 0.10512 |
| 5000 | T3 | A2_STACKELBERG_ONLY | 5 | 0.62517 ± 0.00112 | 0.94874 ± 0.01151 | 0.00163 ± 0.00064 | 0.00008 ± 0.00000 | 0.25968 ± 0.00769 | 28.80583 ± 0.06780 |
| 5000 | T3 | A3_MFG_STACKELBERG | 5 | 0.62581 ± 0.00167 | 0.95409 ± 0.00710 | 0.00178 ± 0.00039 | 0.00030 ± 0.00001 | 0.25936 ± 0.00730 | 28.76729 ± 0.21644 |
| 5000 | T3 | PROPOSED | 5 | 0.62756 ± 0.00251 | 0.95098 ± 0.00888 | 0.00166 ± 0.00042 | 0.00030 ± 0.00002 | 0.25936 ± 0.00922 | 28.77910 ± 0.17052 |

## Paired statistical comparisons

Each comparison uses paired observations for the same load/profile/seed
conditions. The reported difference is Proposed minus the named baseline.
Positive differences are not universally better: interpretation depends on
the metric.

Two-sided paired t-tests are used, with Holm correction across the family
of 18 tests (six metrics and three baselines). Confidence intervals are
95% intervals for the mean paired difference.

| metric | comparison | paired_conditions | mean_difference_proposed_minus_baseline | ci_95_low | ci_95_high | p_value | p_value_holm | significant_holm_0_05 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| utility_mean | PROPOSED_vs_A1_MFG_ONLY | 45 | 0.00204 | 0.00118 | 0.00291 | 0.00002 | 0.00032 | True |
| jain_fairness | PROPOSED_vs_A1_MFG_ONLY | 45 | -0.00151 | -0.00538 | 0.00236 | 0.43672 | 1.00000 | False |
| load_variance | PROPOSED_vs_A1_MFG_ONLY | 45 | -0.00003 | -0.00015 | 0.00008 | 0.56671 | 1.00000 | False |
| allocation_time_seconds | PROPOSED_vs_A1_MFG_ONLY | 45 | 0.00010 | 0.00009 | 0.00011 | 0.00000 | 0.00000 | True |
| throughput | PROPOSED_vs_A1_MFG_ONLY | 45 | -0.00050 | -0.00210 | 0.00111 | 0.53521 | 1.00000 | False |
| response_time_mean | PROPOSED_vs_A1_MFG_ONLY | 45 | -0.05760 | -0.13100 | 0.01581 | 0.12097 | 1.00000 | False |
| utility_mean | PROPOSED_vs_A2_STACKELBERG_ONLY | 45 | 0.00127 | 0.00058 | 0.00197 | 0.00063 | 0.00875 | True |
| jain_fairness | PROPOSED_vs_A2_STACKELBERG_ONLY | 45 | 0.00332 | -0.00061 | 0.00726 | 0.09597 | 1.00000 | False |
| load_variance | PROPOSED_vs_A2_STACKELBERG_ONLY | 45 | -0.00010 | -0.00023 | 0.00003 | 0.14107 | 1.00000 | False |
| allocation_time_seconds | PROPOSED_vs_A2_STACKELBERG_ONLY | 45 | 0.00024 | 0.00023 | 0.00024 | 0.00000 | 0.00000 | True |
| throughput | PROPOSED_vs_A2_STACKELBERG_ONLY | 45 | 0.00174 | 0.00043 | 0.00306 | 0.01051 | 0.13668 | False |
| response_time_mean | PROPOSED_vs_A2_STACKELBERG_ONLY | 45 | 0.03024 | -0.03924 | 0.09973 | 0.38510 | 1.00000 | False |
| utility_mean | PROPOSED_vs_A3_MFG_STACKELBERG | 45 | 0.00189 | 0.00124 | 0.00253 | 0.00000 | 0.00001 | True |
| jain_fairness | PROPOSED_vs_A3_MFG_STACKELBERG | 45 | 0.00174 | -0.00153 | 0.00501 | 0.29004 | 1.00000 | False |
| load_variance | PROPOSED_vs_A3_MFG_STACKELBERG | 45 | -0.00010 | -0.00022 | 0.00001 | 0.08348 | 1.00000 | False |
| allocation_time_seconds | PROPOSED_vs_A3_MFG_STACKELBERG | 45 | -0.00000 | -0.00001 | 0.00001 | 0.76691 | 1.00000 | False |
| throughput | PROPOSED_vs_A3_MFG_STACKELBERG | 45 | -0.00002 | -0.00135 | 0.00132 | 0.97869 | 1.00000 | False |
| response_time_mean | PROPOSED_vs_A3_MFG_STACKELBERG | 45 | -0.04827 | -0.12531 | 0.02876 | 0.21328 | 1.00000 | False |

## Equilibrium diagnostics

| load | policy_variant | run_count | nash_gap_mean | nash_gap_sd | nash_gap_n | nash_deviation_margin_mean | nash_deviation_margin_sd | nash_deviation_margin_n | stackelberg_gap_mean | stackelberg_gap_sd | stackelberg_gap_n | stackelberg_margin_mean | stackelberg_margin_sd | stackelberg_margin_n | stackelberg_deviation_margin_mean | stackelberg_deviation_margin_sd | stackelberg_deviation_margin_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1250 | A1_MFG_ONLY | 15 | 0.00000 | 0.00000 | 15 | -0.00138 | 0.00009 | 15 | N/A | N/A | 0 | N/A | N/A | 0 | N/A | N/A | 0 |
| 1250 | A2_STACKELBERG_ONLY | 15 | N/A | N/A | 0 | N/A | N/A | 0 | 0.00000 | 0.00000 | 15 | 0.00157 | 0.00015 | 15 | -0.00157 | 0.00015 | 15 |
| 1250 | A3_MFG_STACKELBERG | 15 | 0.00000 | 0.00000 | 15 | -0.00311 | 0.00025 | 15 | 0.00000 | 0.00000 | 15 | 0.00140 | 0.00013 | 15 | -0.00140 | 0.00013 | 15 |
| 1250 | PROPOSED | 15 | 0.00000 | 0.00000 | 15 | -0.00462 | 0.00028 | 15 | 0.00000 | 0.00000 | 15 | 0.00148 | 0.00012 | 15 | -0.00148 | 0.00012 | 15 |
| 2500 | A1_MFG_ONLY | 15 | 0.00000 | 0.00000 | 15 | -0.00134 | 0.00009 | 15 | N/A | N/A | 0 | N/A | N/A | 0 | N/A | N/A | 0 |
| 2500 | A2_STACKELBERG_ONLY | 15 | N/A | N/A | 0 | N/A | N/A | 0 | 0.00000 | 0.00000 | 15 | 0.00149 | 0.00010 | 15 | -0.00149 | 0.00010 | 15 |
| 2500 | A3_MFG_STACKELBERG | 15 | 0.00000 | 0.00000 | 15 | -0.00303 | 0.00016 | 15 | 0.00000 | 0.00000 | 15 | 0.00132 | 0.00012 | 15 | -0.00132 | 0.00012 | 15 |
| 2500 | PROPOSED | 15 | 0.00000 | 0.00000 | 15 | -0.00460 | 0.00027 | 15 | 0.00000 | 0.00000 | 15 | 0.00142 | 0.00013 | 15 | -0.00142 | 0.00013 | 15 |
| 5000 | A1_MFG_ONLY | 15 | 0.00000 | 0.00000 | 15 | -0.00147 | 0.00012 | 15 | N/A | N/A | 0 | N/A | N/A | 0 | N/A | N/A | 0 |
| 5000 | A2_STACKELBERG_ONLY | 15 | N/A | N/A | 0 | N/A | N/A | 0 | 0.00000 | 0.00000 | 15 | 0.00160 | 0.00012 | 15 | -0.00160 | 0.00012 | 15 |
| 5000 | A3_MFG_STACKELBERG | 15 | 0.00000 | 0.00000 | 15 | -0.00305 | 0.00015 | 15 | 0.00000 | 0.00000 | 15 | 0.00148 | 0.00022 | 15 | -0.00148 | 0.00022 | 15 |
| 5000 | PROPOSED | 15 | 0.00000 | 0.00000 | 15 | -0.00456 | 0.00030 | 15 | 0.00000 | 0.00000 | 15 | 0.00142 | 0.00014 | 15 | -0.00142 | 0.00014 | 15 |

A2 does not use an MFG follower, and A1 does not use a Stackelberg leader.
Their corresponding equilibrium metrics are not applicable. The gap and
margin values from the current game implementations are candidate-ranking
diagnostics; zero gaps alone do not establish a full Nash or Stackelberg
equilibrium.

## Interpretation cautions

- Overall means combine multiple load levels and priority profiles and are
  descriptive, not a substitute for condition-specific results.
- A statistically significant difference does not by itself establish
  practical importance or universal superiority.
- Paired tests assume the matched differences are sufficiently well behaved
  for a t-test. The 45 matched conditions include repeated profiles and loads,
  so the pooled test should be interpreted alongside condition-level results.
- Jain fairness measures fairness of task allocation counts across nodes,
  not fairness of completed work, resource consumption, or task outcomes.
- Throughput is completed tasks divided by the configured duration in ticks.
- Allocation computation time is measured around the complete policy decision.
  It is not the same as MFG convergence time.

