import { bougiesYahoo } from './yahoo';
import { journalDepot, planDepot, planJournalDepot, statsDepot } from './depot';

export const SOURCES = { bougies: bougiesYahoo, stats: statsDepot, plan: planDepot, journal: journalDepot, planJournal: planJournalDepot };
