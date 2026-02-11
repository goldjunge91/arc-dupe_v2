import vgamepad as vg
import time
import sys

# ==================== GLOBALE GAMEPAD INSTANZ ====================
gamepad = None

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def init_gamepad():
    """Initialisiert das Gamepad einmalig"""
    global gamepad
    print_header("GAMEPAD INITIALISIERUNG")
    try:
        gamepad = vg.VX360Gamepad()
        print("✅ Xbox 360 Controller erfolgreich erstellt")
        print("✅ Controller ist im System registriert")
        return True
    except Exception as e:
        print(f"❌ FEHLER bei Initialisierung: {e}")
        return False

def test_xinput_buttons():
    """Test 1: XInput Buttons (A, B, X, Y)"""
    print_header("TEST: XInput Button Presses")
    print("📋 Buttons: A, B, X, Y")
    print("⏱️  Jeder Button wird 3x gedrückt (0.5s Pause)\n")
    
    buttons = [
        ("A (Jump/Select)", vg.XUSB_BUTTON.XUSB_GAMEPAD_A),
        ("B (Back/Cancel)", vg.XUSB_BUTTON.XUSB_GAMEPAD_B),
        ("X (Reload/Use)", vg.XUSB_BUTTON.XUSB_GAMEPAD_X),
        ("Y (Switch)", vg.XUSB_BUTTON.XUSB_GAMEPAD_Y),
    ]
    
    for btn_name, btn_code in buttons:
        for i in range(3):
            print(f"  → Drücke {btn_name} - #{i+1}")
            gamepad.press_button(button=btn_code) # pyright: ignore[reportOptionalMemberAccess]
            gamepad.update()
            time.sleep(0.1)
            gamepad.release_button(button=btn_code)
            gamepad.update()
            time.sleep(0.5)
    
    print("\n✅ Test abgeschlossen")

def test_raw_input_joysticks():
    """Test 2: Raw Input Joystick Movement"""
    print_header("TEST: Raw Input Joystick Movement")
    print("📋 Left/Right Stick Bewegungen")
    print("⏱️  Jede Richtung wird 2 Sekunden gehalten\n")
    
    movements = [
        ("Left Stick → Rechts", lambda: gamepad.left_joystick_float(x_value_float=1.0, y_value_float=0.0)),
        ("Left Stick → Links", lambda: gamepad.left_joystick_float(x_value_float=-1.0, y_value_float=0.0)),
        ("Left Stick → Oben", lambda: gamepad.left_joystick_float(x_value_float=0.0, y_value_float=1.0)),
        ("Left Stick → Unten", lambda: gamepad.left_joystick_float(x_value_float=0.0, y_value_float=-1.0)),
        ("Right Stick → Rechts", lambda: gamepad.right_joystick_float(x_value_float=1.0, y_value_float=0.0)),
        ("Right Stick → Links", lambda: gamepad.right_joystick_float(x_value_float=-1.0, y_value_float=0.0)),
    ]
    
    for movement_name, movement_func in movements:
        print(f"  → {movement_name}")
        
        # Kontinuierlicher Input-Stream (60 FPS für 2 Sekunden)
        for _ in range(120):  # 2 Sekunden bei 60 FPS
            movement_func()
            gamepad.update()
            time.sleep(0.016)  # ~60 FPS
        
        # Zurück zur Neutralposition
        gamepad.left_joystick_float(0.0, 0.0)
        gamepad.right_joystick_float(0.0, 0.0)
        gamepad.update()
        time.sleep(0.5)
    
    print("\n✅ Test abgeschlossen")

def test_triggers():
    """Test 3: Trigger (LT/RT) Input"""
    print_header("TEST: Trigger Input (LT/RT)")
    print("📋 Left/Right Trigger")
    print("⏱️  Jeder Trigger wird 3x aktiviert\n")
    
    for i in range(3):
        print(f"  → Left Trigger (LT) - #{i+1}")
        gamepad.left_trigger_float(value_float=1.0)
        gamepad.update()
        time.sleep(0.3)
        gamepad.left_trigger_float(value_float=0.0)
        gamepad.update()
        time.sleep(0.3)
        
        print(f"  → Right Trigger (RT) - #{i+1}")
        gamepad.right_trigger_float(value_float=1.0)
        gamepad.update()
        time.sleep(0.3)
        gamepad.right_trigger_float(value_float=0.0)
        gamepad.update()
        time.sleep(0.3)
    
    print("\n✅ Test abgeschlossen")

def test_dpad():
    """Test 4: D-Pad Input"""
    print_header("TEST: D-Pad Input")
    print("📋 D-Pad (Oben, Unten, Links, Rechts)")
    print("⏱️  Jede Richtung wird 2x gedrückt\n")
    
    directions = [
        ("D-Pad Oben", vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP),
        ("D-Pad Unten", vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN),
        ("D-Pad Links", vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT),
        ("D-Pad Rechts", vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT),
    ]
    
    for dir_name, dir_code in directions:
        for i in range(2):
            print(f"  → {dir_name} - #{i+1}")
            gamepad.press_button(button=dir_code)
            gamepad.update()
            time.sleep(0.1)
            gamepad.release_button(button=dir_code)
            gamepad.update()
            time.sleep(0.4)
    
    print("\n✅ Test abgeschlossen")

def test_combo_input():
    """Test 5: Kombinierte Inputs"""
    print_header("TEST: Kombinierte Inputs")
    print("📋 Joystick + Button gleichzeitig")
    print("⏱️  Simulation: Bewegung + Sprung\n")
    
    for i in range(3):
        print(f"  → Kombination #{i+1}: Links laufen + A drücken")
        
        # Stick nach links + A Button
        gamepad.left_joystick_float(x_value_float=-0.8, y_value_float=0.0)
        gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        gamepad.update()
        time.sleep(0.2)
        
        gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        gamepad.update()
        time.sleep(0.3)
        
        # Zurück zu neutral
        gamepad.left_joystick_float(0.0, 0.0)
        gamepad.update()
        time.sleep(0.5)
    
    print("\n✅ Test abgeschlossen")

def test_continuous_jump():
    """Test 6: Kontinuierliches Springen (Infinite Loop)"""
    print_header("TEST: Kontinuierliches Springen")
    print("📋 Automatisches A-Button Drücken")
    print("⏱️  Läuft bis STRG+C gedrückt wird\n")
    print("⚠️  Drücke STRG+C zum Beenden\n")
    
    try:
        counter = 0
        while True:
            counter += 1
            print(f"  → Sprung #{counter}")
            
            gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
            gamepad.update()
            time.sleep(0.1)
            
            gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
            gamepad.update()
            time.sleep(1.0)
            
            # Keep-Alive für Hardware-ID
            gamepad.left_joystick_float(x_value_float=0.0001, y_value_float=0.0001) # type: ignore
            gamepad.update()
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test vom Benutzer gestoppt")
        # Neutralposition
        gamepad.left_joystick_float(0.0, 0.0) # type: ignore
        gamepad.update()

def show_test_menu():
    """Zeigt das Testauswahl-Menü"""
    print("\n" + "█"*60)
    print("  VERFÜGBARE TESTS:")
    print("█"*60)
    print("\n  [1] XInput Buttons (A, B, X, Y)")
    print("  [2] Raw Input Joysticks (Left/Right Stick)")
    print("  [3] Triggers (LT, RT)")
    print("  [4] D-Pad (Oben, Unten, Links, Rechts)")
    print("  [5] Combo Input (Stick + Button)")
    print("  [6] Kontinuierliches Springen (Infinite Loop)")
    print("  [7] ALLE Tests nacheinander")
    print("  [0] Beenden")
    print("\n" + "="*60)

def run_tests(choices):
    """Führt die gewählten Tests aus"""
    test_map = {
        '1': ("XInput Buttons", test_xinput_buttons),
        '2': ("Raw Input Joysticks", test_raw_input_joysticks),
        '3': ("Triggers", test_triggers),
        '4': ("D-Pad", test_dpad),
        '5': ("Combo Input", test_combo_input),
        '6': ("Kontinuierliches Springen", test_continuous_jump),
    }
    
    if '7' in choices:
        # Alle Tests außer Infinite Loop
        choices = ['1', '2', '3', '4', '5']
    
    for choice in choices:
        if choice in test_map:
            test_name, test_func = test_map[choice]
            test_func()
            if choice != '6':  # Pause nach jedem Test (außer Infinite Loop)
                time.sleep(2)

def main():
    print("\n" + "█"*60)
    print("  VIGEM CONTROLLER - INTERAKTIVER TEST")
    print("█"*60)
    
    # Schritt 1: Initialisierung
    if not init_gamepad():
        print("\n❌ Abbruch: Gamepad konnte nicht initialisiert werden")
        return
    
    # Schritt 2: Testauswahl
    show_test_menu()
    
    while True:
        choice = input("\nWähle Test(s) [z.B. 1,2,3 oder 7 für alle]: ").strip()
        
        if choice == '0':
            print("\n👋 Programm beendet")
            return
        
        choices = [c.strip() for c in choice.split(',')]
        
        # Validierung
        valid_choices = [c for c in choices if c in ['1','2','3','4','5','6','7']]
        
        if not valid_choices:
            print("❌ Ungültige Eingabe. Bitte 0-7 wählen.")
            continue
        
        break
    
    # Schritt 3: Warten auf joy.cpl
    print("\n" + "="*60)
    print("  JOY.CPL SETUP")
    print("="*60)
    print("\n📋 ANWEISUNGEN:")
    print("  1. Öffne joy.cpl:")
    print("     → Windows-Taste + R")
    print("     → Tippe: joy.cpl")
    print("     → ENTER drücken")
    print("\n  2. Doppelklick auf 'Xbox 360 Controller for Windows'")
    print("\n  3. Gehe zum 'Test' Tab")
    print("\n  4. Lass das Fenster AKTIV (nicht minimieren!)")
    print("\n⚠️  WICHTIG: joy.cpl muss im Vordergrund bleiben!")
    print("\n")
    
    input("Drücke ENTER wenn joy.cpl bereit ist...")
    
    # Schritt 4: Tests ausführen
    print("\n🚀 Starte Tests...\n")
    time.sleep(1)
    
    try:
        run_tests(valid_choices)
        
        print("\n" + "█"*60)
        print("  ALLE TESTS ABGESCHLOSSEN")
        print("█"*60)
        
        print("\n📊 NÄCHSTE SCHRITTE:")
        print("  ✅ Wenn Inputs in joy.cpl sichtbar waren:")
        print("     → Controller funktioniert perfekt!")
        print("     → Kann jetzt in quickdupe.py integriert werden")
        print("\n  ❌ Wenn KEINE Inputs sichtbar waren:")
        print("     → joy.cpl war nicht aktiv/minimiert")
        print("     → Oder: Anti-Virus blockiert ViGEmBus")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Fehler während Tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Programm vom Benutzer abgebrochen")
    except Exception as e:
        print(f"\n\n❌ Kritischer Fehler: {e}")
        import traceback
        traceback.print_exc()