/** Heure de Paris sans dépendre d'Intl (heure d'été : du dernier dimanche de mars au dernier dimanche d'octobre, 1h UTC). */

const HEURE = 3_600_000;

function dernierDimanche(annee: number, mois: number): number {
  const fin = Date.UTC(annee, mois + 1, 0, 1); // dernier jour du mois, 1h UTC
  return fin - new Date(fin).getUTCDay() * 24 * HEURE;
}

export function decalageParis(ms: number): number {
  const a = new Date(ms).getUTCFullYear();
  return ms >= dernierDimanche(a, 2) && ms < dernierDimanche(a, 9) ? 2 * HEURE : HEURE;
}

export interface HeureParis {
  /** AAAA-MM-JJ */
  date: string;
  heure: number;
  minute: number;
  /** 0 dimanche … 6 samedi */
  jour: number;
}

export function paris(ms: number): HeureParis {
  const d = new Date(ms + decalageParis(ms));
  return { date: d.toISOString().slice(0, 10), heure: d.getUTCHours(), minute: d.getUTCMinutes(), jour: d.getUTCDay() };
}

/** Instant UTC (ms) d'une heure de Paris donnée. */
export function depuisParis(date: string, heure: number, minute = 0): number {
  const approx = Date.parse(`${date}T00:00:00Z`) + heure * HEURE + minute * 60_000;
  return approx - decalageParis(approx - HEURE);
}

export function hhmm(p: HeureParis): string {
  return `${String(p.heure).padStart(2, '0')}h${String(p.minute).padStart(2, '0')}`;
}

const JOURS = ['dim.', 'lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.'];
const MOIS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];

export function dateFr(date: string): string {
  const d = new Date(`${date}T12:00:00Z`);
  return `${JOURS[d.getUTCDay()]} ${d.getUTCDate()} ${MOIS[d.getUTCMonth()]}`;
}
