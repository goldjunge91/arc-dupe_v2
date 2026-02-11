import random
import time


def vary_time(base_seconds, variance_pct=0):
    """Apply fixed absolute variance. 10%=±0.1ms, 40%=±1ms, 100%=±4ms.

    base_seconds is interpreted as seconds.
    """
    if base_seconds <= 0 or variance_pct <= 0:
        return base_seconds
    max_delta = 0.004 * (variance_pct / 100.0) ** 1.5
    return max(0.001, base_seconds + random.uniform(-max_delta, max_delta))


def vary_ms(ms, variance_pct=0):
    """Apply percentage variance to an ms timing value and return new ms (int/float)."""
    if variance_pct == 0 or ms <= 0:
        return ms
    max_delta = ms * variance_pct / 100.0
    delta = random.uniform(-max_delta, max_delta)
    return max(1, ms + delta)


def vary_balanced(ms, count, variance_pct=0):
    """Generate 'count' delays that each vary but sum to exactly ms*count.
    Returns list of delays in ms.
    """
    if variance_pct == 0 or count <= 1:
        return [ms] * count

    max_delta = ms * variance_pct / 100.0
    deltas = [random.uniform(-max_delta, max_delta) for _ in range(count)]
    avg_delta = sum(deltas) / count
    deltas = [d - avg_delta for d in deltas]
    return [max(1, ms + d) for d in deltas]


def vsleep(ms, stop_check=None, variance_pct=0, chunk_ms=50):
    """Sleep for ms with optional variance and a stop predicate.

    stop_check is a callable returning True when sleep should abort early.
    """
    total_ms = vary_ms(ms, variance_pct)
    if total_ms <= 0:
        return
    elapsed = 0
    while elapsed < total_ms:
        if stop_check and stop_check():
            return
        sleep_time = min(chunk_ms, total_ms - elapsed)
        time.sleep(sleep_time / 1000.0)
        elapsed += sleep_time


def clear_stale_stop_flags(obj):
    """Clear stop flags on an object for macros that aren't running.

    Expects object to have attributes like `mine_running` and `mine_stop`.
    """
    try:
        if hasattr(obj, 'mine_running') and not getattr(obj, 'mine_running'):
            setattr(obj, 'mine_stop', False)
        if hasattr(obj, 'triggernade_running') and not getattr(obj, 'triggernade_running'):
            setattr(obj, 'triggernade_stop', False)
        if hasattr(obj, 'espam_running') and not getattr(obj, 'espam_running'):
            setattr(obj, 'espam_stop', False)
        if hasattr(obj, 'untitled_running') and not getattr(obj, 'untitled_running'):
            setattr(obj, 'untitled_stop', False)
        if hasattr(obj, 'untitled2_running') and not getattr(obj, 'untitled2_running'):
            setattr(obj, 'untitled2_stop', False)
        if hasattr(obj, 'kd_running') and not getattr(obj, 'kd_running'):
            setattr(obj, 'kd_stop', False)
    except Exception:
        pass
