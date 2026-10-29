/** Version web (aperçu) : pas de notifications ni de tâche de fond. */
import type { Resume } from '../domain';

export async function prevenir(_resumes: Resume[]): Promise<number> {
  return 0;
}

export async function activerAlertes(): Promise<boolean> {
  return false;
}
