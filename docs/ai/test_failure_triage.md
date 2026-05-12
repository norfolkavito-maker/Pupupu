# Test Failure Triage - Stage 03 Bridge Verification

## Summary
Total failing tests: 11
Total skipped tests: 2
Total passed tests: 202

## Failure Analysis

### Category 1: Mock/Context Issues (7 failures)
**Root cause:** Test mocks expecting old ctx structure vs new mock structure.

| Test File | Test Name | Exact Error | Likely Cause | Related to Stage 03 changes | Action |
|------------|-----------|-------------|--------------|---------------------------|--------|
| `tests/test_wf_inference_unittest.py` | `test_infer_wf_tcp_single` | `AttributeError: 'types.SimpleNamespace' object has no attribute 'data_dir'` | YES - Mock ctx missing data_dir | Fix mock structure |
| `tests/test_wf_inference_unittest.py` | `test_infer_wf_tcp_union_dedup_sort` | `AttributeError: 'types.SimpleNamespace' object has no attribute 'data_dir'` | YES - Mock ctx missing data_dir | Fix mock structure |
| `tests/test_wf_inference_unittest.py` | `test_infer_wf_udp` | `AttributeError: 'types.SimpleNamespace' object has no attribute 'data_dir'` | YES - Mock ctx missing data_dir | Fix mock structure |
| `tests/test_wf_inference_unittest.py` | `test_existing_wf_not_duplicated` | `AttributeError: 'types.SimpleNamespace' object has no attribute 'data_dir'` | YES - Mock ctx missing data_dir | Fix mock structure |
| `tests/test_winws2_compat_unittest.py` | `test_build_command_uses_winws2_when_engine_winws2` | `AttributeError: 'types.SimpleNamespace' object has no attribute 'flowseal_lists_dir'` | YES - Mock ctx missing flowseal_lists_dir | Fix mock structure |
| `tests/test_test_all_strategies_with_progress_unittest.py` | `test_quick_mode_builtin_only` | `TypeError: TestAllStrategiesWithProgress.test_quick_mode_builtin_only.<locals>._ls() got multiple values for argument 'kind'` | YES - Test method signature conflict | Fix test method |
| `tests/test_test_all_strategies_with_progress_unittest.py` | `test_quick_mode_builtin_only` | `TypeError: TestAllStrategiesWithProgress.test_quick_mode_builtin_only.<locals>._ls() got multiple values for argument 'kind'` | YES - Test method signature conflict | Fix test method |

### Category 2: Old Strategy Constructor (3 failures)
**Root cause:** Tests still using old `args=` parameter instead of new `commands=[Command(...)]` format.

| Test File | Test Name | Exact Error | Likely Cause | Related to Stage 03 changes | Action |
|------------|-----------|-------------|--------------|---------------------------|--------|
| `tests/test_wf_inference_unittest.py` | `test_dv1_like_sample_gets_wf_tcp` | `TypeError: Strategy.__init__() got an unexpected keyword argument 'args'` | YES - Old constructor usage | Update to commands format |
| `tests/test_winws2_compat_unittest.py` | `test_build_command_uses_winws2_when_engine_winws2` | `TypeError: Strategy.__init__() got an unexpected keyword argument 'args'` | YES - Old constructor usage | Update to commands format |
| `tests/test_model_unittest.py` | `test_get_full_args_basic` | `TypeError: Strategy.__init__() missing 1 required positional argument: 'id'` | YES - Missing required id parameter | Add id parameter |

### Category 3: Masking Test Issues (3 failures)
**Root cause:** Masking tests expecting old behavior vs new mask implementation.

| Test File | Test Name | Exact Error | Likely Cause | Related to Stage 03 changes | Action |
|------------|-----------|-------------|--------------|---------------------------|--------|
| `tests/test_mask_secrets_unittest.py` | `test_masks_password_in_dict` | `AssertionError: 'secret' != '***'` | YES - Mask implementation changed | Update test expectations |
| `tests/test_mask_secrets_unittest.py` | `test_masks_uuid` | `AssertionError: '123e4567-****-****-****-4000' not found in 'id=123e****************************4000'` | YES - Mask implementation changed | Update test expectations |
| `tests/test_mask_secrets_unittest.py` | `test_masks_vless_link` | `AssertionError: 'vless://***@' not found in 'vless://123e4**********************************************************=none'` | YES - Mask implementation changed | Update test expectations |

### Category 4: SingBox Node Issues (1 failure)
**Root cause:** SingBox tests expecting old mask behavior.

| Test File | Test Name | Exact Error | Likely Cause | Related to Stage 03 changes | Action |
|------------|-----------|-------------|--------------|---------------------------|--------|
| `tests/test_singbox_nodes_unittest.py` | `test_save_masks_raw` | `AssertionError: 'vless://***@' not found in [...]` | YES - Mask implementation changed | Update test expectations |

## Recommended Actions

### Priority 1: Fix Mock/Context Issues
The mock objects in test files need to be updated to match the new ctx structure used by the actual code.

### Priority 2: Fix Strategy Constructor Issues
Update remaining tests to use the new `commands=[Command(...)]` format with required `id` parameter.

### Priority 3: Update Masking Test Expectations
Update masking tests to match the new mask implementation behavior.

### Priority 4: Fix SingBox Test Expectations
Update SingBox tests to work with the new mask implementation.

## Blockers
- **Full pytest passing:** Blocked by 11 failing tests requiring mock updates and constructor fixes.
- **Stage 04 readiness:** NO - Cannot proceed while relevant tests are failing.

## Next Steps
1. Fix mock context structures in failing test files
2. Update remaining Strategy constructor calls
3. Update masking test expectations
4. Re-run full pytest verification
5. Update PROGRESS.md with honest status
6. Update BLOCKERS.md if needed
