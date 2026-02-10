import threading
import time
import pydivert


_pydivert = None  # Lazy loaded
_handle = None
_on = False

_tamper_handle = None
_tamper_on = False
_tamper_patterns = [0x64, 0x13, 0x88, 0x40, 0x1F, 0xA0, 0xAA, 0x55]


def start_packet_drop(outbound=True, inbound=True):
    """DROP PACKETS NOW"""
    global _handle, _on, _pydivert
    if _on:
        return

    if _pydivert is None:
        import pydivert

        _pydivert = pydivert

    if outbound and inbound:
        filt = "outbound or inbound"  # Clumsy's exact filter
    elif outbound:
        filt = "outbound"
    else:
        filt = "inbound"

    try:
        _handle = _pydivert.WinDivert(filt)
        _handle.open()
        _on = True
        threading.Thread(target=_drop_loop, daemon=True).start()
        time.sleep(0.015)  # Match Clumsy's keypress toggle delay
    except:
        _on = False
        _handle = None


def _drop_loop():
    global _on
    while _on:
        try:
            if _handle:
                _handle.recv()  # recv but don't send = drop
            else:
                break
        except:
            break
    _on = False


def stop_packet_drop():
    """STOP DROPPING NOW"""
    global _handle, _on
    if not _on:
        return
    h = _handle
    _handle = None
    _on = False
    if h:
        try:
            h.close()
        except:
            pass
    time.sleep(0.05)  # Give thread time to exit


def is_dropping():
    return _on


def start_packet_tamper(outbound=True, inbound=True):
    """Start tampering packets - corrupt data but still send"""
    global _tamper_handle, _tamper_on, _pydivert
    if _tamper_on:
        return

    if _pydivert is None:
        import pydivert

        _pydivert = pydivert

    if outbound and inbound:
        filt = "outbound or inbound"
    elif outbound:
        filt = "outbound"
    else:
        filt = "inbound"

    try:
        _tamper_handle = _pydivert.WinDivert(filt)
        _tamper_handle.open()
        _tamper_on = True
        threading.Thread(target=_tamper_loop, daemon=True).start()
        print(f"[TAMPER] Started tampering packets ({filt})")
    except Exception as e:
        print(f"[TAMPER] Failed to start: {e}")
        _tamper_on = False
        _tamper_handle = None


def _tamper_loop():
    global _tamper_on
    while _tamper_on and _tamper_handle:
        try:
            packet = _tamper_handle.recv()
            if packet and packet.payload:
                payload = bytearray(packet.payload)
                for i in range(len(payload)):
                    payload[i] ^= _tamper_patterns[i % 8]
                packet.payload = bytes(payload)
            _tamper_handle.send(packet)
        except:
            break


def stop_packet_tamper():
    """Stop tampering packets"""
    global _tamper_handle, _tamper_on
    if not _tamper_on:
        return
    _tamper_on = False
    if _tamper_handle:
        try:
            _tamper_handle.close()
        except:
            pass
        _tamper_handle = None
    print("[TAMPER] Stopped")


def is_tampering():
    return _tamper_on
