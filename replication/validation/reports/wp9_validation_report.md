# Work Package 9 - Unified Monte Carlo and Computational Validation

## Scope and execution

WP9 consolidates the numerical evidence for WP3-WP8 into one executable repository. The verified command is:

```bash
make wp9
```

The clean one-command run completed in **67.1 seconds** from source commit `3c1f9091ae7934f689ccff4dc80ede7e903b3e78`.

## Design correction

For the Dirichlet heat equation on `(0,1)`, `lambda_N Delta = pi^2 N^2 / n`. Only **1 of 25** cells in the original Cartesian design satisfy the operational resolution threshold `lambda_N Delta <= 0.15`. The high-replication core therefore uses `(N,n) = (5,2000), (10,8000), (20,32000)`, with 1,000 replications per design and common `lambda_N Delta = 0.123370`.

## Estimation and LAN

|   N |     n |   lambda_N_Delta |   theta_bias |   theta_rmse |   theta_empirical_sd |   theta_average_se |   sigma_bias |   sigma_rmse |   sigma_empirical_sd |   sigma_average_se |   ztheta_sd |   zsigma_sd |   scaled_cross_correlation |
|----:|------:|-----------------:|-------------:|-------------:|---------------------:|-------------------:|-------------:|-------------:|---------------------:|-------------------:|------------:|------------:|---------------------------:|
|   5 |  2000 |          0.12337 |   0.0034138  |    0.024162  |            0.023931  |          0.023704  |   6.5813e-05 |   0.0021344  |           0.0021344  |         0.0021218  |     1.018   |     1.0062  |                   0.074631 |
|  10 |  8000 |          0.12337 |   0.00044815 |    0.0090863 |            0.0090798 |          0.0088947 |   2.4151e-05 |   0.00074927 |           0.00074925 |         0.00075006 |     1.0219  |     0.999   |                   0.096596 |
|  20 | 32000 |          0.12337 |  -9.863e-05  |    0.0032527 |            0.0032528 |          0.0032531 |   6.9246e-06 |   0.00026392 |           0.00026396 |         0.00026517 |     0.99952 |     0.99546 |                   0.12221  |

The largest absolute deviation of an information-standardised empirical standard deviation from one is **0.0219**.

## Counterfactual targets and simultaneous coverage

|   N |     n |   cdf_sup_rmse |   effect_sup_rmse |   fast_simultaneous_coverage |   slow_simultaneous_coverage |   fast_average_full_width |   slow_average_full_width |   pointwise_coverage_min |   pointwise_coverage_max |
|----:|------:|---------------:|------------------:|-----------------------------:|-----------------------------:|--------------------------:|--------------------------:|-------------------------:|-------------------------:|
|   5 |  2000 |     0.0017202  |         0.016385  |                        0.946 |                        0.95  |                0.0067066  |                 0.063739  |                    0.945 |                        1 |
|  10 |  8000 |     0.00060432 |         0.0062865 |                        0.955 |                        0.948 |                0.0023713  |                 0.02417   |                    0.955 |                        1 |
|  20 | 32000 |     0.00021286 |         0.0022607 |                        0.951 |                        0.951 |                0.00083837 |                 0.0088563 |                    0.951 |                        1 |

Regional pointwise coverage:

|   N |     n | region   |    mean |   min |   max |
|----:|------:|:---------|--------:|------:|------:|
|   5 |  2000 | centre   | 0.96467 | 0.947 | 1     |
|   5 |  2000 | shoulder | 0.946   | 0.946 | 0.946 |
|   5 |  2000 | tail     | 0.945   | 0.945 | 0.945 |
|  10 |  8000 | centre   | 0.97    | 0.955 | 1     |
|  10 |  8000 | shoulder | 0.955   | 0.955 | 0.955 |
|  10 |  8000 | tail     | 0.957   | 0.957 | 0.957 |
|  20 | 32000 | centre   | 0.96733 | 0.951 | 1     |
|  20 | 32000 | shoulder | 0.951   | 0.951 | 0.951 |
|  20 | 32000 | tail     | 0.953   | 0.953 | 0.953 |

## Bootstrap sensitivity

| sensitivity_axis   | method          |   draws |   grid_size |   fast_coverage |   slow_coverage |   fast_mean_full_width |   slow_mean_full_width |
|:-------------------|:----------------|--------:|------------:|----------------:|----------------:|-----------------------:|-----------------------:|
| multiplier         | direct_gaussian |     499 |          31 |         0.93333 |         0.93    |              0.0023507 |               0.024123 |
| multiplier         | mode_gaussian   |     499 |          31 |         0.96    |         0.94667 |              0.0030209 |               0.034239 |
| multiplier         | mode_rademacher |     499 |          31 |         0.95667 |         0.94667 |              0.002943  |               0.032795 |
| draw_count         | direct_gaussian |     199 |          31 |         0.94    |         0.93667 |              0.0023499 |               0.023849 |
| draw_count         | direct_gaussian |     999 |          31 |         0.94    |         0.92667 |              0.002375  |               0.024149 |
| grid_resolution    | direct_gaussian |     499 |          11 |         0.93333 |         0.92667 |              0.0023606 |               0.02407  |
| grid_resolution    | direct_gaussian |     499 |          61 |         0.93667 |         0.92    |              0.0023694 |               0.024103 |

At 300 replications, the Monte Carlo standard error of coverage near 0.95 is approximately 0.013. The direct Gaussian multiplier is preferred when the limiting information is known; mode-block Gaussian and Rademacher versions provide structural robustness.

## Galerkin rates

|   alpha_q | metric         |   predicted_slope |   empirical_slope |   ci_low |   ci_high |   r_squared |
|----------:|:---------------|------------------:|------------------:|---------:|----------:|------------:|
|      0    | mean_error     |              -2.6 |           -2.5801 |  -2.5954 |   -2.5648 |     0.99999 |
|      0    | variance_error |              -4.6 |           -4.5642 |  -4.5952 |   -4.5332 |     0.99999 |
|      0    | strong_rms     |              -2.3 |           -2.3066 |  -2.3113 |   -2.302  |     1       |
|      0    | cdf_sup        |              -2.6 |           -2.5801 |  -2.5954 |   -2.5648 |     0.99999 |
|      0.75 | mean_error     |              -2.6 |           -2.5801 |  -2.5954 |   -2.5648 |     0.99999 |
|      0.75 | variance_error |              -6.1 |           -6.0821 |  -6.2595 |   -5.9048 |     0.99991 |
|      0.75 | strong_rms     |              -2.6 |           -2.5865 |  -2.5983 |   -2.5748 |     0.99999 |
|      0.75 | cdf_sup        |              -2.6 |           -2.5801 |  -2.5954 |   -2.5648 |     0.99999 |
|      1.5  | mean_error     |              -2.6 |           -2.5801 |  -2.5954 |   -2.5648 |     0.99999 |
|      1.5  | variance_error |              -7.6 |           -8.2822 | -15.38   |   -1.1845 |     0.99547 |
|      1.5  | strong_rms     |              -2.6 |           -2.5801 |  -2.5954 |   -2.5649 |     0.99999 |
|      1.5  | cdf_sup        |              -2.6 |           -2.5801 |  -2.5954 |   -2.5648 |     0.99999 |

The temporal diagnostic produces fitted first-order slopes between approximately 0.994 and 0.999.

## Statistical-numerical balance

|   N |     n |   empirical_balancing_K |   theoretical_balancing_K |
|----:|------:|------------------------:|--------------------------:|
|   5 |  2000 |                      12 |                         6 |
|  10 |  8000 |                      20 |                         9 |
|  20 | 32000 |                      30 |                        13 |

The experiment reports the correct plateau/balance structure: truncation bias approaches the statistical floor. It does not manufacture a U-shape in a model where known spectral structure prevents variance inflation from target extrapolation.

## Operator sensitivity

The central finite-difference error decreases from `4.270e-06` at `epsilon=0.1` to `1.708e-09` at `epsilon=0.002`. The law-linearisation remainder is quadratic and the Gaussian Wasserstein distance remains below the common-noise Lipschitz envelope.

## Non-identification

| construction          | metric                                  |       value |
|:----------------------|:----------------------------------------|------------:|
| adapted_feedback      | factual_variance_gap                    | 0           |
| adapted_feedback      | counterfactual_KS                       | 0.0359147   |
| adapted_feedback      | counterfactual_W2                       | 0.0339894   |
| exogenous_one_time    | forcing_variance_model_1                | 0.715532    |
| exogenous_one_time    | forcing_variance_model_2                | 1.75777     |
| exogenous_one_time    | factual_variance_gap                    | 5.55112e-17 |
| exogenous_one_time    | counterfactual_KS                       | 0.0984347   |
| exogenous_one_time    | counterfactual_W2                       | 0.291043    |
| exogenous_finite_grid | minimum_eigenvalue_K1                   | 2.35335     |
| exogenous_finite_grid | minimum_eigenvalue_K2                   | 5.15393     |
| exogenous_finite_grid | factual_covariance_frobenius_gap        | 8.18457e-16 |
| exogenous_finite_grid | counterfactual_covariance_frobenius_gap | 0.700334    |
| unknown_calibration   | factual_sensor_variance_gap             | 0           |
| unknown_calibration   | field_counterfactual_KS                 | 0.161337    |
| unknown_calibration   | sensor_counterfactual_variance_gap      | 0           |
| crossworld_coupling   | effect_variance_rho_0                   | 1           |
| crossworld_coupling   | effect_variance_rho_0.8                 | 0.266788    |
| crossworld_coupling   | effect_variance_rho_-0.5                | 1.45826     |

The four-time open-loop construction has factual covariance gap `8.185e-16` and post-intervention covariance gap `0.7003`.

## Completion gate

| criterion                      | passed   |     diagnostic |
|:-------------------------------|:---------|---------------:|
| theorem_aligned_designs        | True     |    0.12337     |
| at_least_1000_reps             | True     | 1000           |
| standardised_sd_near_one       | True     |    0.0218731   |
| simultaneous_coverage_reported | True     |    7           |
| rate_slopes_checked            | True     |    0.682205    |
| operator_remainder_checked     | True     |    4.67479e-08 |
| failure_cases_demonstrated     | True     |    0.700334    |
| planned_grid_audited           | True     |    1           |
| one_command_runner             | True     |    1           |

All conditions pass. WP1-WP9 are complete; WP10 manuscript reconstruction remains.
