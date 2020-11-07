import numpy as np
import os
import cv2
from PIL import Image
import dlib

img = np.load("sonuc_np/001.jpg.npy")

#dairevi gezme algoritması
#sol omuz için sola doğru gidiş için üst pikselden sol piksel yönünde yani
#saat yönü tersi araştırma: yukarı, sola, aşağı, aşağı, sağa,
yonSol = ((-1, 0), (0, -1), (1, 0), (1, 0), (0, 1))
#saat yönü araştırma: yukarı, sağa, aşağı, aşağı, sola
yonSag = ((-1, 0), (0, 1), (1, 0), (1, 0), (0, -1))

def CoordinateLeftBottomtoNPLeftTop(x, y, h):
    #return  h-y, x
    return  h-y-1, x


#np.arrray şeklinde x -> satır sırası,
#y -> sütün sayısı olacak şekilde gelir, h yükselik
#np.array sisteminde ilk indeks yani x, 2d koordinattaki y'ye denk gelir
#orijin sol alt köşe yapılır

def NPLeftToptoCoordinateLeftBottom(satir, sutun, h):
    #return  sutun, h-satir
    return  sutun, h-satir-1

def omuzGezerDaireviLimitli(maske: np.array, omuzKulunc: dlib.dpoint, yon, limit, ikiNoktaArasiMesafe=4) -> dlib.dpoint:
    # merdiven algosu
    noktalar = []
    height, width = maske.shape[0], maske.shape[1]
    satir, sutun = CoordinateLeftBottomtoNPLeftTop(int(round(omuzKulunc.x)), int(round(omuzKulunc.y)), height)
    noktalar.append(np.array([satir, sutun]))
    oncekiSatir, oncekiSutun = satir, sutun
    yedekSatir, yedekSutun = satir, sutun
    tespitVar = False
    sinirDisi = False

    while True:
        tespitVar = False
        sinirDisi = False
        yedekSatir, yedekSutun = satir, sutun
        #print(satir,sutun)
        for (sat, sut) in yon:
            satir = satir + sat
            sutun = sutun + sut
            if not (sutun >= 0 and sutun < width and satir >= 0 and satir < height):  # sınır dışına çıkma kontrolu
                sinirDisi = True
                break
            if maske[satir, sutun] == 15:  # yeni nokta tespit edilmiş demektir
                if satir == oncekiSatir and sutun == oncekiSutun:
                    continue
                oncekiSatir, oncekiSutun = yedekSatir, yedekSutun
                tespitVar = True
                break
        if sinirDisi or not tespitVar:
            break

        # burraya geldiyse tespit var demektirl
        mesafe = np.linalg.norm(noktalar[-1] - np.array([satir, sutun]))
        if mesafe >= ikiNoktaArasiMesafe:
            if limit < satir:  # eğer limitin aşağısında bir nokta bulduysak eklemeden çık
                break
            noktalar.append(np.array([satir, sutun]))
    return [dlib.dpoint(NPLeftToptoCoordinateLeftBottom(x, y, height)) for (x, y) in noktalar]


#///////////////////////////////////

#2d koordinattan np array koordinatına
#orijin sol üst köşe yapılır
#Dikkat! x, y integer verilmelidir


def kafaBul(maske:np.array): #sağdan ve soldan tarayarak orta nokta bulunur
    height, width = maske.shape[0], maske.shape[1]

    solNokta = []
    sagNokta = []
    #sol taraf
    for i in range(height):
        for j in range(width):
            if maske[i,j] == 15:
                solNokta=[i,j]
                break
        if len(solNokta) >= 1:
            break

    for i in range(height):
        for j in range(width-1,0,-1):
            if maske[i,j] == 15:
                sagNokta=[i,j]
                break
        if len(sagNokta) >= 1:
            break

    #orta nokta
    fark = sagNokta[1]-solNokta[1]
    nokta= dlib.point(solNokta[1]+int(fark/2),height-solNokta[0])

    return nokta

def arrayAdd(dizi1,dizi2):

    allNokta = dizi1 + dizi2

    return allNokta

def numpyCevir(noktalar:list): #fitellipse fonksiyonunun girdi tipine çevrilir

    liste = []
    for i in range(len(noktalar)-1):
        liste.append([[noktalar[i][0],noktalar[i][1]]])
    array = np.array(liste)
    return array

def dlipToN(bulunanNoktalar,maske): #bulunan noktalar simetri almak için çevrilir

    height, width = maske.shape[0], maske.shape[1]
    allNokta = []
    for i in range(len(bulunanNoktalar)):
        allNokta.append([int(bulunanNoktalar[i].x),height-int(bulunanNoktalar[i].y)])

    return allNokta

def takeSecond(elem):#sıralama yapma
    return elem[1]

def simetriAl(noktalar): #bulunan en son noktaya göre simetri alır

    list = []
    sıralıNoktalar=sorted(noktalar,key=takeSecond)
    simetriNoktası = sıralıNoktalar[len(sıralıNoktalar)-1][1]

    for i in range(len(sıralıNoktalar)-1):
        fark = simetriNoktası-sıralıNoktalar[i][1]

        list.append([sıralıNoktalar[i][0],simetriNoktası+fark])

    return sıralıNoktalar+list

def kafaTespit(img:np.array):


        height, width = img.shape[0], img.shape[1]
        ortX = kafaBul(img).y
        baslangıc=height-ortX

        for limit in range(height,baslangıc,-1): #limit azaltma // Bazı resimlerde dikey elips oluşmuyor.ilk dikey ellipsleri tespit etmek için limit azaltma

            noktalar = numpyCevir(simetriAl(arrayAdd(dlipToN(omuzGezerDaireviLimitli(img, kafaBul(img), yonSol, limit), img),
                                                    dlipToN(omuzGezerDaireviLimitli(img, kafaBul(img), yonSag, limit), img))))
            try:        #hata ayıklama
                ellipse = cv2.fitEllipse(noktalar)
            except:
                continue

            widthE = ellipse[1][0]
            heightE = ellipse[1][1]

            oran = round(heightE/widthE,2)

            if  oran > 1.00 and oran < 1.35:

                resim = np.array(img * 255, dtype=np.uint8)

                son = cv2.ellipse(resim, ellipse, (23, 184, 80), 2)

                cv2.polylines(resim, noktalar, 1, (255, 255, 255), 2)

                cv2.imshow("img", son)

                cv2.waitKey(0)
                cv2.destroyAllWindows()
                break
            else:
                continue

kafaTespit(img)
