import cv2

def start_camera():
    # Initialize the default laptop camera (0)
    cap = cv2.VideoCapture(0)

    # Prevent Runtime Errors if the camera is blocked or unavailable
    if not cap.isOpened():
        print("Error: Could not open webcam. Check your permissions.")
        return

    print("Webcam initialized. Press 'q' to close the window.")

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        
        if not ret:
            print("Error: Failed to grab frame. Exiting...")
            break
            
        # Display the live frame
        cv2.imshow('Stress Detection - Live Feed', frame)

        # Break the loop if the 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Clean up and release hardware resources
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_camera()