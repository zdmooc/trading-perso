import { useColorScheme } from 'react-native';

const clair = {
  fond: '#F6F7F9', carte: '#FFFFFF', texte: '#1B1F24', doux: '#6B7280', ligne: '#E5E7EB',
  vert: '#1A8A5A', rouge: '#D93A3F', bleu: '#3B7BEA', orange: '#D48A06', gris: '#8B949E', actif: 'rgba(76,141,255,0.08)',
};
const sombre: typeof clair = {
  fond: '#0D1117', carte: '#161B22', texte: '#E6EDF3', doux: '#8B949E', ligne: '#30363D',
  vert: '#22A06B', rouge: '#E5484D', bleu: '#4C8DFF', orange: '#F5A524', gris: '#8B949E', actif: 'rgba(76,141,255,0.12)',
};

export type Couleurs = typeof clair;

export function useCouleurs(): Couleurs {
  return useColorScheme() === 'dark' ? sombre : clair;
}

export const espace = (n: number) => n * 4;
