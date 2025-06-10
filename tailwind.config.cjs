/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
    './app/**/*.{js,ts,jsx,tsx}', // Si tu utilises le répertoire app/
  ],
  theme: {
    extend: {
      colors: {
        primary: 'var(--primary-color)',        // Utilisation de la variable CSS pour la couleur primaire
        secondary: 'var(--secondary-color)',    // Utilisation de la variable CSS pour la couleur secondaire
        background: 'var(--background-color)',  // Utilisation de la variable CSS pour le fond
        foreground: 'var(--foreground-color)',  // Utilisation de la variable CSS pour le texte de premier plan
        filezone: 'var(--filezone-color)',      // Utilisation de la variable CSS pour la zone de fichier
        dark: 'var(--dark-color)',              // Utilisation de la variable CSS pour la couleur sombre
      },
    },
  },
  plugins: [],
};
