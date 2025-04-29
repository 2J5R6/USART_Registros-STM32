import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# Definir la función f(x) para el caso (b)
def f_b(x):
    return x**2

# Función para calcular los coeficientes de Fourier
def calc_fourier_coeffs_b(n_terms, L=2):
    # a0 = 1/L * int_{-L}^{L} x^2 dx
    a0 = 1/(2*L) * np.integrate.quad(lambda x: x**2, -L, L)[0]
    
    a = np.zeros(n_terms)
    b = np.zeros(n_terms)
    
    for n in range(1, n_terms+1):
        # an = 1/L * int_{-L}^{L} x^2 * cos(n*pi*x/L) dx
        a[n-1] = 1/L * np.integrate.quad(lambda x: x**2 * np.cos(n*np.pi*x/L), -L, L)[0]
        
        # bn = 1/L * int_{-L}^{L} x^2 * sin(n*pi*x/L) dx
        b[n-1] = 1/L * np.integrate.quad(lambda x: x**2 * np.sin(n*np.pi*x/L), -L, L)[0]
    
    return a0, a, b

# Función para calcular la suma parcial de la serie de Fourier
def fourier_sum_b(x, a0, a, b, L=2):
    result = a0
    for n in range(1, len(a)+1):
        result += a[n-1] * np.cos(n*np.pi*x/L) + b[n-1] * np.sin(n*np.pi*x/L)
    return result

# Calcular coeficientes y graficar para diferentes valores de N
def plot_fourier_b(N_values=[5, 10, 15, 25]):
    fig = plt.figure(figsize=(14, 10))
    gs = GridSpec(2, 2, figure=fig)
    
    x = np.linspace(-2, 2, 1000)
    y_exact = f_b(x)
    
    for i, N in enumerate(N_values):
        ax = fig.add_subplot(gs[i//2, i%2])
        
        a0, a, b = calc_fourier_coeffs_b(N)
        y_approx = fourier_sum_b(x, a0, a, b)
        
        ax.plot(x, y_exact, 'b-', label='f(x) exacta')
        ax.plot(x, y_approx, 'r-', label=f'Suma parcial (N={N})')
        
        ax.set_title(f'Aproximación de Fourier con N = {N}')
        ax.set_xlabel('x')
        ax.set_ylabel('f(x)')
        ax.grid(True)
        ax.legend()
    
    plt.tight_layout()
    plt.show()

# Ejecutar para los valores requeridos
plot_fourier_b()

# También podemos calcular los coeficientes analíticamente
# Para x^2 en [-L,L], se puede demostrar que:
# a0 = 2L^2/3
# an = 4L^2/(n^2*pi^2) * (-1)^n
# bn = 0 (debido a que x^2 es una función par)

def analytical_coeffs_b(n_terms, L=2):
    a0 = 2*L**2/3
    a = np.array([4*L**2/(n**2*np.pi**2) * (-1)**n for n in range(1, n_terms+1)])
    b = np.zeros(n_terms)  # Todos son cero por ser función par
    return a0, a, b