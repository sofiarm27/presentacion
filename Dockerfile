# ==========================================
# Etapa 1: Build de la app React/Vite
# ==========================================
FROM node:20-alpine as build

# Directorio de trabajo en el contenedor
WORKDIR /app

# Copiar archivos de dependencias
COPY package.json package-lock.json ./

# Instalar dependencias
RUN npm ci

# Copiar el código fuente
COPY ./ ./

# Argumento para la URL de la API que Railway inyectará
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Construir la versión de producción
# Vite incrustará VITE_API_URL durante este paso
RUN npm run build

# ==========================================
# Etapa 2: Servir con Nginx (ligero y rápido)
# ==========================================
FROM nginx:alpine

# Copiar configuración de Nginx para manejar rutas de React (SPA)
# Esto asegura que React Router funcione al actualizar la página
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar el build compilado del frontend a Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Nginx corre en el puerto 80 por defecto
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
