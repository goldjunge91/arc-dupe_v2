"""
Test script to measure Clumsy's disconnect/reconnect timing in detail.
Press SPACE to trigger a full cycle: bracket press -> disconnect -> bracket press -> reconnect
"""
import socket
import time
import threading
import keyboard
import statistics

# Config
TARGET_HOST = "8.8.8.8"  # Google DNS
TARGET_PORT = 53

running = True
all_results = []

def test_packet():
    """Send a packet and return (success, rtt_ms)"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.05)  # 50ms timeout
    try:
        start = time.perf_counter()
        sock.sendto(b"x", (TARGET_HOST, TARGET_PORT))
        # For UDP we can't really measure RTT without a response
        # But sendto failing = dropped
        end = time.perf_counter()
        return True, (end - start) * 1000
    except:
        return False, 0
    finally:
        sock.close()

def run_test():
    global all_results

    print("\n" + "=" * 60)
    print("STARTING DETAILED TEST CYCLE")
    print("=" * 60)

    # Check starting state
    ok, _ = test_packet()
    if not ok:
        print("WARNING: Already disconnected! Press [ to reconnect first.")
        return

    result = {}

    # Measure baseline RTT
    print("\n[0] Measuring baseline (10 packets)...")
    baseline_rtts = []
    for _ in range(10):
        ok, rtt = test_packet()
        if ok:
            baseline_rtts.append(rtt)
        time.sleep(0.01)
    if baseline_rtts:
        result['baseline_rtt_avg'] = statistics.mean(baseline_rtts)
        result['baseline_rtt_min'] = min(baseline_rtts)
        result['baseline_rtt_max'] = max(baseline_rtts)
        print(f"    Baseline RTT: avg={result['baseline_rtt_avg']:.2f}ms min={result['baseline_rtt_min']:.2f}ms max={result['baseline_rtt_max']:.2f}ms")

    # ========== DISCONNECT ==========
    print("\n[1] Pressing [ to DISCONNECT...")
    keypress_time = time.perf_counter()
    keyboard.press_and_release('[')

    # Rapid-fire packets to catch exact moment of disconnect
    packets_before_drop = 0
    first_drop_time = None
    while True:
        ok, _ = test_packet()
        now = time.perf_counter()
        if ok:
            packets_before_drop += 1
        else:
            first_drop_time = now
            break
        if now - keypress_time > 2.0:
            print("    TIMEOUT waiting for disconnect")
            return
        time.sleep(0.001)  # 1ms between checks

    result['disconnect_delay_ms'] = (first_drop_time - keypress_time) * 1000
    result['packets_before_drop'] = packets_before_drop
    print(f"    DISCONNECTED after {result['disconnect_delay_ms']:.2f}ms ({packets_before_drop} packets got through)")

    # Count dropped packets while disconnected
    print("\n[2] Waiting 500ms while disconnected...")
    dropped_count = 0
    dc_start = time.perf_counter()
    while time.perf_counter() - dc_start < 0.5:
        ok, _ = test_packet()
        if not ok:
            dropped_count += 1
        time.sleep(0.002)
    result['packets_dropped'] = dropped_count
    print(f"    Dropped {dropped_count} packets in 500ms")

    # ========== RECONNECT ==========
    print("\n[3] Pressing [ to RECONNECT...")
    keypress_time = time.perf_counter()
    keyboard.press_and_release('[')

    # Rapid-fire packets to catch exact moment of reconnect
    packets_before_reconnect = 0
    first_success_time = None
    while True:
        ok, _ = test_packet()
        now = time.perf_counter()
        if not ok:
            packets_before_reconnect += 1
        else:
            first_success_time = now
            break
        if now - keypress_time > 2.0:
            print("    TIMEOUT waiting for reconnect")
            return
        time.sleep(0.001)

    result['reconnect_delay_ms'] = (first_success_time - keypress_time) * 1000
    result['packets_before_reconnect'] = packets_before_reconnect
    print(f"    RECONNECTED after {result['reconnect_delay_ms']:.2f}ms ({packets_before_reconnect} packets dropped)")

    # Post-reconnect RTT
    print("\n[4] Measuring post-reconnect RTT...")
    time.sleep(0.1)
    post_rtts = []
    for _ in range(10):
        ok, rtt = test_packet()
        if ok:
            post_rtts.append(rtt)
        time.sleep(0.01)
    if post_rtts:
        result['post_rtt_avg'] = statistics.mean(post_rtts)
        print(f"    Post-reconnect RTT: avg={result['post_rtt_avg']:.2f}ms")

    # ========== REPORT ==========
    all_results.append(result)

    print("\n" + "=" * 60)
    print("TEST RESULTS:")
    print("=" * 60)
    print(f"  Disconnect delay:     {result['disconnect_delay_ms']:.2f}ms")
    print(f"  Reconnect delay:      {result['reconnect_delay_ms']:.2f}ms")
    print(f"  Total toggle time:    {result['disconnect_delay_ms'] + result['reconnect_delay_ms']:.2f}ms")
    print(f"  Packets before drop:  {result['packets_before_drop']}")
    print(f"  Packets dropped:      {result['packets_dropped']} (in 500ms)")
    print("=" * 60)

    if len(all_results) > 1:
        avg_dc = statistics.mean([r['disconnect_delay_ms'] for r in all_results])
        avg_rc = statistics.mean([r['reconnect_delay_ms'] for r in all_results])
        print(f"\nAVERAGE OVER {len(all_results)} TESTS:")
        print(f"  Disconnect: {avg_dc:.2f}ms")
        print(f"  Reconnect:  {avg_rc:.2f}ms")

    print("\nPress SPACE to run another test, ESC to quit")

print("=" * 60)
print("CLUMSY DETAILED TIMING TEST")
print("=" * 60)
print("Make sure Clumsy is running with [ as toggle hotkey")
print("Press SPACE to run a full disconnect/reconnect test")
print("Press ESC to quit")
print("=" * 60)

# Quick connection check
ok, _ = test_packet()
print(f"\nConnection status: {'CONNECTED' if ok else 'DISCONNECTED'}")
print("Ready! Press SPACE to test...\n")

keyboard.add_hotkey('space', run_test)

try:
    keyboard.wait('esc')
except:
    pass

running = False
print("\nDone.")
