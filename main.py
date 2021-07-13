from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *
from OpenGL.arrays import vbo
import sys, math, os
import numpy as np

EXIT = -1
FIRST = 0
WIDTH = 500
HEIGHT = 500

angle = 0.0
axis = [0, 0, 1]
startP = 0, 0, 0
actOri = np.matrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
shadowColor = (0.5, 0.5, 0.5, 0.0)

doRotation = False
doMove = False
doZoom = False
doOrtho = True
doPersp = False
doWire = False
doSolid = True
doPoints = False
doShadow = False

actZoom = 0
zoomTmp = 0

delaAngle = 5
xAngle = 0
yAngle = 0
zAngle = 0
faces = []
scale = 0.0

backgroundColor = (1.0, 1.0, 1.0, 0.0)
objectColor = (1.0, 1.0, 1.0, 0.0)

light = (0.0, 10.0,0.0)

xPos, yPos = 0, 0
xAct, yAct = 0, 0


def changeBG(color):
    global backgroundColor
    backgroundColor = color
    glClearColor(*backgroundColor)

def changeFG(color):
    global objectColor
    objectColor = color

changeColor = changeFG

def normalenBerechnen():
   nnsProPunkt = [[0,0,0] for c in vertices]
   for face in faces:
      vtx1idx = int(face[0][0]) - 1
      vtx2idx = int(face[1][0]) - 1
      vtx3idx = int(face[2][0]) - 1

      a = np.array(vertices[vtx1idx])
      b = np.array(vertices[vtx2idx])
      c = np.array(vertices[vtx3idx])

      ab = np.subtract(b,a)
      ac = np.subtract(c,a)

      nn = np.cross(ab, ac)

      nnsProPunkt[vtx1idx] += nn
      nnsProPunkt[vtx2idx] += nn
      nnsProPunkt[vtx3idx] += nn

   return nnsProPunkt

def init(width, height):
    """ Initialize an OpenGL window """
    glClearColor(*backgroundColor)           #background color
    glMatrixMode(GL_PROJECTION)              #switch to projection matrix
    glLoadIdentity()

    glOrtho(-1.5, 1.5, -1.5, 1.5, -1.0, 1.0) #multiply with new p-matrix
    glMatrixMode(GL_MODELVIEW)               #switch to modelview matrix
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_NORMALIZE)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)

    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glEnable(GL_COLOR_MATERIAL)


def projectOnSphere(x, y, r):
    x, y = x - WIDTH/2.0, HEIGHT/2.0-y
    a = min(r*r, x**2 + y**2)
    z = math.sqrt(r*r - a)
    l = math.sqrt(x**2 + y**2 + z**2)
    print(x/l, y/l, z/l)
    return x/l, y/l, z/l


def rotate(angle, axis):
    #rotationsmatrix bauen
    c, mc = math.cos(angle), 1-math.cos(angle)
    s = math.sin(angle)
    l = math.sqrt(np.dot(np.array(axis), np.array(axis)))
    x, y, z = np.array(axis)/l
    r = np.matrix([[x*x*mc+c, x*y*mc-z*s, x*z*mc+y*s, 0],
                    [x*y*mc+z*s, y*y*mc+c, y*z*mc-x*s, 0],
                    [x*z*mc-y*s, y*z*mc+x*s, z*z*mc+c, 0],
                    [0, 0, 0, 1]])

    return r.transpose()


def display():
    """ Render all objects"""
    p = [1.0, 0, 0, 0, 0, 1.0, 0, -1.0 / yLight, 0, 0, 1.0, 0, 0, 0, 0, 0]
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()


    glScale(scalefactor, scalefactor, scalefactor)
    glTranslate(-center[0], -center[1], -center[2])

    myVbo.bind()

    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_NORMAL_ARRAY)

    glVertexPointer(3, GL_FLOAT, 24, myVbo)
    glNormalPointer(GL_FLOAT, 24, myVbo+12)


    glMultMatrixf(np.array(actOri * rotate(angle, axis)))
    glTranslate(xPos, yPos, 0.0)

    if doShadow:
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glColor(shadowColor)
        glTranslatef(xLight, yLight, zLight)
        glTranslate(0.0, boundingBox[0][1], 0.0)
        glMultMatrixf(p)
        glTranslate(0.0, -boundingBox[0][1], 0.0)
        glTranslatef(-xLight, -yLight, -zLight)
        glDrawArrays(GL_TRIANGLES, 0, len(data))
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glPopMatrix()

    glColor(objectColor)
    glDrawArrays(GL_TRIANGLES, 0, len(data))
    myVbo.unbind()

    glDisableClientState(GL_VERTEX_ARRAY)

    glDisableClientState(GL_NORMAL_ARRAY)

    glutSwapBuffers()


def reshape(width, height):
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    if doOrtho:
        if width == height:
            glOrtho(-1.5 + scale, 1.5 - scale, -1.5 + scale, 1.5 - scale, -10.0, 10.0)
        elif width <= height:
           glOrtho(-1.5+scale, 1.5-scale,
                   (-1.5+scale)*height/width, (1.5-scale)*height/width,
                   -10.0, 10.0)
        else:
            glOrtho((-1.5 + scale) * width/height, (1.5 - scale) * width/height, -1.5 + scale, 1.5 - scale,
                    -10.0, 10.0)
    if doPersp:
        if width <= height:
            gluPerspective(45.0*(height/width), float(width) / height, 0.1, 100.0)
        else:
            gluPerspective(45.0, float(width) / height, 0.1, 100.0)
        gluLookAt(0, 0, 3 + scale, 0, 0, 0, 0, 1, 0)
    glMatrixMode(GL_MODELVIEW)


def keyPressed(key, x, y):
    """ handle keypress events """
    global xAngle, yAngle, zAngle, doPersp, doOrtho, modelcolor, doShadow, doBackground, doForeground, changeColor
    availableColors = {b's': (0.0, 0.0, 0.0, 0.0),
                       b'w': (1.0, 1.0, 1.0, 0.0),
                       b'r': (1.0, 0.0, 0.0, 0.0),
                       b'g': (1.0, 1.0, 0.0, 0.0),
                       b'b': (0.0, 0.0, 1.0, 0.0)}
    if key == b'\x1b':
        sys.exit()
    if key == b'x':
        xAngle += delaAngle
    if key == b'X':
        xAngle -= delaAngle
    if key == b'y':
        yAngle += delaAngle
    if key == b'Y':
        yAngle -= delaAngle
    if key == b'z':
        zAngle += delaAngle
    if key == b'Z':
        zAngle -= delaAngle

    if key == b'p':
        doPersp= True
        doOrtho = False
        reshape(WIDTH, HEIGHT)

    if key == b'o':
        doPersp = False
        doOrtho= True
        reshape(WIDTH, HEIGHT)

    if key == b'c':
        changeColor = changeBG if changeColor == changeFG else changeFG

    if key == b'h':
        if doShadow:
            doShadow = False
            reshape(WIDTH, HEIGHT)
        else:
            doShadow = True
            reshape(WIDTH, HEIGHT)

    if key in availableColors:
        changeColor(availableColors[key])


    glutPostRedisplay()


def mousebuttonpressed(button, state, x, y):
    global startP, actOri, angle, doRotation, doMove, xAct, yAct, scale, doZoom, actZoom, zoomTmp
    glutDetachMenu(GLUT_RIGHT_BUTTON)
    r = min(WIDTH, HEIGHT)/2.0
    if button == GLUT_LEFT_BUTTON:
        if state == GLUT_DOWN:
            doRotation = True
            startP = projectOnSphere(x, y, r)
        if state == GLUT_UP:
            doRotation = False
            actOri = actOri*rotate(angle, axis)
            angle = 0
    if button == GLUT_MIDDLE_BUTTON:
        if state == GLUT_DOWN:
            doZoom = True
            startP = (x, y)
        elif state == GLUT_UP:
            doZoom = False
            actZoom += zoomTmp
            zoomTmp = 0
    if button == GLUT_RIGHT_BUTTON:
        if state == GLUT_DOWN:
            doMove = True
            xAct, yAct=x,y
        if state == GLUT_UP:
            xAct += xPos
            yAct += yPos
            doMove = False


def mousemoved(x, y):
    global angle, axis, scalefactor, xPos, yPos, xAct, yAct, scale, zoomTmp
    if doRotation:
        r = min(WIDTH, HEIGHT)/2.0
        moveP = projectOnSphere(x, y, r)
        angle = math.acos(np.dot(startP, moveP))
        axis = np.cross(startP, moveP)
        glutPostRedisplay()
    if doMove:
        #xPos = (x -xAct)/min(WIDTH, HEIGHT)
        xPos = (x - xAct)*3
        #print xPos
        #yPos = (yAct -y)/min(WIDTH, HEIGHT)
        yPos = (yAct -y)*3
        glutPostRedisplay()
    if doZoom:
        zoomTmp = startP[1] - y

        scalefactor *= zoomTmp

        glutPostRedisplay()


def mouse(button, state, x, y):
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        pass


def mouseMotion(x,y):
    pass


def menu_func(value):
    if value == EXIT:
       sys.exit()
    glutPostRedisplay()

def animate():
    global angle
    angle = (angle + delaAngle) % 360
    glutPostRedisplay()


def main():
    global WIDTH
    global HEIGHT
    cwd = os.getcwd()
    glutInit(sys.argv)
    os.chdir(cwd)

    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIDTH, HEIGHT)
    glutCreateWindow("CG Abgabe 2 (Blatt 7)")

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyPressed)

    glutMouseFunc(mousebuttonpressed)
    glutMotionFunc(mousemoved)
    glutCreateMenu(menu_func)

    glutAddMenuEntry("First Entry", FIRST)
    glutAddMenuEntry("EXIT", EXIT)
    glutAttachMenu(GLUT_RIGHT_BUTTON)

    init(WIDTH, HEIGHT)

    glutMainLoop()


if __name__ == "__main__":

    global vertices, xLight, yLight, zLight
    global data
    global scalefactor
    global center
    global vtxNormal
    global vbo
    global boundingBox


    with open(sys.argv[1], 'r', encoding='utf-8') as file:

        file_lines = file.readlines()
        lines = list(file_lines)

        vertices = [list(map(float, (l.split())[1:])) for l in lines if l.startswith("v ")]
        #file.seek(0)
        texVertices = [list(map(float, (l.split())[1:]))for l in lines if l.startswith("vt")]

        vtxNormal = [list(map(float, (l.split())[1:])) for l in lines if l.startswith("vn")]

        if not texVertices and not vtxNormal:
            faces = []
            for line in lines:
                if line.startswith("f"):
                    a = line.split()[1:]
                    li = []
                    for e in a:
                        lis = [e, None, None]
                        li.append(lis)
                    faces.append(li)

        elif not texVertices:
            faces = [[list(map(int, str(e).split("//"))) for e in (line.split())[1:]] for line in lines if
                 line.startswith("f")]
            for lis in faces:
                lis[0].insert(1, None)
                lis[1].insert(1, None)
                lis[2].insert(1, None)

        else:
            faces = [[list(map(float, str(e).split("/"))) for e in (line.split())[1:]] for line in lines if
                 line.startswith("f")]

    mini = list(map(min, list(zip(*vertices))))

    maxi = list(map(max, list(zip(*vertices))))

    print(vertices)
    boundingBox = list(map(min, list(zip(*vertices)))), list(map(max, list(zip(*vertices))))
    print("bounding", boundingBox)

    center = (np.array(list(boundingBox[0])) + np.array(list(boundingBox[1]))) / 2

    scalefactor = 2.0 / max(np.array(boundingBox[1]) - np.array(boundingBox[0]))

    xLight = (boundingBox[1][1] - boundingBox[0][1]) * 2
    yLight = (boundingBox[1][1] - boundingBox[0][1]) * 5
    zLight = (boundingBox[1][1] - boundingBox[0][1]) * 2

    if not vtxNormal:
        normals = normalenBerechnen()

    data = []
    for face in faces:
        for vertex in face:
            vn = int(vertex[0]) - 1

            if vtxNormal:
                nn = int(vertex[2]) - 1
                data.append(vertices[vn])
                data.append(vtxNormal[nn])
            else:
                data.append(vertices[vn] + normals[vn].tolist())

    myVbo = vbo.VBO(np.array(data, 'f'))

    main()