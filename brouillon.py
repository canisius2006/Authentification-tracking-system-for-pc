import cv2

# Ouverture de la caméra
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Appliquer l'effet miroir horizontal (gauche/droite)
    mirrored_frame = cv2.flip(frame, 1)

    # Affichage des deux versions pour comparer
    cv2.imshow("Originale", frame)
    cv2.imshow("Effet Miroir", mirrored_frame)

    # Quitter avec la touche 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()