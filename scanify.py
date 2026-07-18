#!/usr/bin/env python3
"""Transforma foto de documento A4 em imagem com aparencia de escaneado:
detecta a folha, corrige perspectiva (remove fundo/borda) e uniformiza a iluminacao."""
import sys
import os
import cv2
import numpy as np

A4_RATIO = 297.0 / 210.0  # altura / largura


def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]      # topo-esquerda
    rect[2] = pts[np.argmax(s)]      # base-direita
    d = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(d)]      # topo-direita
    rect[3] = pts[np.argmax(d)]      # base-esquerda
    return rect


def find_page(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, np.ones((15, 15), np.uint8))
    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    c = max(contours, key=cv2.contourArea)
    if cv2.contourArea(c) < 0.25 * img.shape[0] * img.shape[1]:
        return None
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.02 * peri, True)
    if len(approx) == 4:
        return order_points(approx.reshape(4, 2).astype("float32"))
    box = cv2.boxPoints(cv2.minAreaRect(c))
    return order_points(box.astype("float32"))


def warp_to_a4(img, quad, out_width=1240):
    out_height = int(round(out_width * A4_RATIO))
    dst = np.array([[0, 0], [out_width - 1, 0],
                    [out_width - 1, out_height - 1], [0, out_height - 1]],
                   dtype="float32")
    M = cv2.getPerspectiveTransform(quad, dst)
    return cv2.warpPerspective(img, M, (out_width, out_height),
                               flags=cv2.INTER_CUBIC)


def scan_effect(img, strength=1.35):
    # nivelar iluminacao: divide cada canal pelo "fundo" (blur grande)
    bg = cv2.medianBlur(img, 51)
    norm = cv2.divide(img.astype(np.float32), bg.astype(np.float32) + 1e-6)
    norm = np.clip(norm * 255.0, 0, 255)
    # ponto branco em 238: elimina sombras leves e o vazamento do verso
    # sem apagar logos em cinza-claro
    norm = np.clip(norm * (255.0 / 238.0), 0, 255)
    # reforcar o traco: escurece o que nao e fundo
    out = 255.0 - np.clip((255.0 - norm) * strength, 0, 255)
    out = np.clip(out, 0, 255).astype(np.uint8)
    # leve nitidez
    blur = cv2.GaussianBlur(out, (0, 0), 1.0)
    out = cv2.addWeighted(out, 1.4, blur, -0.4, 0)
    # regioes onde o fundo original era escuro (mesa/sombra, nao papel):
    # a divisao gera ruido colorido ali — pintar de branco
    bg_gray = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
    dark = (bg_gray < 110).astype(np.uint8) * 255
    dark = cv2.dilate(dark, np.ones((9, 9), np.uint8))
    out[dark > 0] = (255, 255, 255)
    # borda branca fina: remove franjas de cor onde sobrou fundo da mesa
    m = max(8, out.shape[0] // 150)
    out = cv2.copyMakeBorder(out[m:-m, m:-m], m, m, m, m,
                             cv2.BORDER_CONSTANT, value=(255, 255, 255))
    return out


def process(path, out_dir):
    img = cv2.imread(path)
    if img is None:
        return path, "ERRO: nao consegui abrir"
    quad = find_page(img)
    if quad is None:
        return path, "AVISO: folha nao detectada, aplicado apenas efeito de scanner"
    warped = warp_to_a4(img, quad)
    result = scan_effect(warped)
    name = os.path.splitext(os.path.basename(path))[0] + ".jpg"
    out_path = os.path.join(out_dir, name)
    cv2.imwrite(out_path, result, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return path, f"OK -> {out_path}"


if __name__ == "__main__":
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)
    for p in sys.argv[2:]:
        src, msg = process(p, out_dir)
        print(f"{os.path.basename(src)}: {msg}")
