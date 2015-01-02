# Bojan Nikolic <b.nikolic@mrao.cam.ac.uk>
# 
# Synthetise and image interfometer data

import numpy
import scipy.special

def ucs(m):
    return numpy.mgrid[-1:1:(m.shape[0]*1j), -1:1:(m.shape[1]*1j)]

def uax(m, n, eps=0):
    "1D Array which spans nth axes of m with values between -1 and 1"
    return numpy.mgrid[(-1+eps):(1-eps):(m.shape[n]*1j)]

def aaf(a, m, c):
    """Compute the anti-aliasing function as separable product. See VLA
    Scientific Memoranda 129, 131, 132 

    """
    sx,sy=map(lambda i: scipy.special.pro_ang1(m,m,c,uax(a,i,eps=1e-10))[0],
           [0,1])
    return numpy.outer(sx,sy)

def wkern(a, T2, w):
    "W convolution kernel. T2 is half-width of map in radian"
    r2=((ucs(a)*T2)**2).sum(axis=0)
    ph=w*(1-numpy.sqrt(1-r2))
    return (numpy.exp(2j*numpy.pi*ph))

def sample(a, p):
    "Take samples from array a"
    x=((1+p[:,0])*a.shape[0]/2).astype(int)
    y=((1+p[:,1])*a.shape[1]/2).astype(int)
    return a[x,y]

def grid(a, aw, p, v):
    "Grid samples array a without convolution"
    x=((1+p[:,0])*a.shape[0]/2).astype(int)
    y=((1+p[:,1])*a.shape[1]/2).astype(int)
    for i in range(len(x)):
        a[x[i],y[i]] += v[i]
        aw[x[i],y[i]] +=1
    return a, aw

def convgridone(a, aw, pi, gcf, v):
    "Convolve and grid one sample"
    sx, sy= gcf.shape[0]/2, gcf.shape[1]/2
    a[ pi[0]-sx: pi[0]+sx+1,  pi[1]-sy: pi[1]+sy+1 ] += gcf*v
    #aw[ pi[0]-sx: pi[0]+sx+1,  pi[1]-sy: pi[1]+sy+1 ] += numpy.abs(gcf)
    #aw[ pi[0]-sx: pi[0]+sx+1,  pi[1]-sy: pi[1]+sy+1 ] += 1
    aw[ pi[0],  pi[1] ] += 1

def convgrid(a, aw, p, v, gcf):
    "Grid after convolving with gcf" 
    x=((1+p[:,0])*a.shape[0]/2).astype(int)
    y=((1+p[:,1])*a.shape[1]/2).astype(int)
    for i in range(len(x)):
        convgridone(a, aw, (x[i], y[i]), gcf, v[i])
    return a, aw    

def exmid(a, s):
    "Extract a section from middle of a map"
    cx=a.shape[0]/2
    cy=a.shape[1]/2
    return a[cx-s:cx+s+1, cy-s:cy+s+1]

def div0(a1, a2):
    "Divide a1 by a2 except pixels where a2 is zero"
    m= (a2!=0)
    res=a1.copy()
    res[m]/=a2[m]
    return res

def inv(g, w):
    return numpy.fft.ifft2(numpy.fft.ifftshift(div0(g,w)))

def rotv(p, l, m, v):
    "Rotate visibilities to direction (l,m)"
    s=numpy.array([l, m , numpy.sqrt(1 - l**2 - m**2)])
    return (v * numpy.exp(2j*numpy.pi*numpy.dot(p, s)))    
    
def rotw(p, v):
    "Rotate visibilities to zero w plane"
    return rotv(p, 0, 0, v)

def sortw(p, v):
    zs=numpy.argsort(p[:,2])
    return p[zs], v[zs]

def simpleimg(T2, L2, p, v):
    N= T2*L2 *4
    guv=numpy.zeros([N, N], dtype=complex)
    gw =numpy.zeros([N, N])
    grid(guv, gw, p/L2, rotw(p, v))
    return guv, gw

def wslicimg(T2, L2, p, v,
             wstep=2000):
    "Basic w-projection by w-sort and slicing in w" 
    N= T2*L2 *4
    guv=numpy.zeros([N, N], dtype=complex)
    gw =numpy.zeros([N, N], dtype=complex)
    p, v = sortw(p, v)
    v=rotw(p,v)
    nv=len(v)
    ii=range( 0, nv, wstep)
    ir=zip(ii[:-1], ii[1:]) + [ (ii[-1], nv) ]
    wgl=[]
    for ilow, ihigh in ir:
        w=p[ilow:ihigh,2].mean()
        wk=wkern(guv, T2 , w)
        wg=exmid(numpy.fft.fftshift(numpy.fft.fft2(wk)),15)
        wgl.append(wg)
        convgrid(guv, gw, p[ilow:ihigh]/L2, v[ilow:ihigh],  wg)
    return guv, gw, wgl
    
    
    



