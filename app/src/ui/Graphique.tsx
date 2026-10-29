import { useState } from 'react';
import { View } from 'react-native';
import Svg, { Line, Polyline, Rect, Text as SvgText } from 'react-native-svg';
import { type Bougie, nombre } from '../domain';
import { useCouleurs } from './theme';

export interface Niveau {
  y: number;
  couleur: string;
  texte: string;
  tirets?: boolean;
}

export interface Serie {
  valeurs: (number | null)[];
  couleur: string;
}

const DROITE = 74; // place des étiquettes de prix
const HAUT = 8;
const BAS = 8;

/** Bougies, niveaux horizontaux (entrées, stops, objectifs, pivots) et courbes (moyennes). */
export function Graphique({ bougies, niveaux = [], series = [], hauteur = 240 }: { bougies: Bougie[]; niveaux?: Niveau[]; series?: Serie[]; hauteur?: number }) {
  const c = useCouleurs();
  const [largeur, setLargeur] = useState(0);
  const prix = [...bougies.flatMap((b) => [b.h, b.l]), ...series.flatMap((s) => s.valeurs.filter((v): v is number => v !== null))];
  if (!bougies.length) return null;
  let lo = Math.min(...prix), hi = Math.max(...prix);
  // Les niveaux trop loin du cours écraseraient le graphique : on ne garde que les proches.
  const marge = (hi - lo) * 0.6 + 1;
  const visibles = niveaux.filter((n) => n.y >= lo - marge && n.y <= hi + marge);
  for (const n of visibles) {
    lo = Math.min(lo, n.y);
    hi = Math.max(hi, n.y);
  }
  const w = Math.max(largeur - DROITE, 1);
  const pas = w / bougies.length;
  const y = (v: number) => HAUT + ((hi - v) / (hi - lo || 1)) * (hauteur - HAUT - BAS);
  const corps = Math.max(1, pas * 0.65);
  return (
    <View onLayout={(e) => setLargeur(e.nativeEvent.layout.width)} style={{ height: hauteur }}>
      {largeur > 0 && (
        <Svg width={largeur} height={hauteur}>
          {bougies.map((b, i) => {
            const x = i * pas + pas / 2;
            const coul = b.c >= b.o ? c.vert : c.rouge;
            return [
              <Line key={`m${i}`} x1={x} x2={x} y1={y(b.h)} y2={y(b.l)} stroke={coul} strokeWidth={1} />,
              <Rect key={`c${i}`} x={x - corps / 2} width={corps} y={y(Math.max(b.o, b.c))} height={Math.max(1, Math.abs(y(b.o) - y(b.c)))} fill={coul} />,
            ];
          })}
          {series.map((s, k) => (
            <Polyline key={`s${k}`} fill="none" stroke={s.couleur} strokeWidth={1.5}
              points={s.valeurs.map((v, i) => (v === null ? null : `${i * pas + pas / 2},${y(v)}`)).filter(Boolean).join(' ')} />
          ))}
          {visibles.map((n, k) => [
            <Line key={`l${k}`} x1={0} x2={w} y1={y(n.y)} y2={y(n.y)} stroke={n.couleur} strokeWidth={1.2} strokeDasharray={n.tirets ? '4 3' : undefined} />,
            <SvgText key={`t${k}`} x={w + 4} y={y(n.y) + 4} fontSize={10} fill={n.couleur}>{`${n.texte} ${nombre(n.y, 0)}`}</SvgText>,
          ])}
          <SvgText x={w + 4} y={y(bougies[bougies.length - 1].c) + 4} fontSize={10} fontWeight="bold" fill={c.texte}>
            {nombre(bougies[bougies.length - 1].c, 0)}
          </SvgText>
        </Svg>
      )}
    </View>
  );
}
