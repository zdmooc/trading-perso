/**
 * Alertes sur le téléphone : notifications locales, vérifiées à chaque actualisation de l'écran et, app fermée,
 * par une tâche de fond Android (au mieux toutes les 15 minutes, quand le système le permet).
 * Lecture seule : aucune notification ne passe d'ordre.
 */
import { Platform } from 'react-native';
import * as BackgroundTask from 'expo-background-task';
import * as Notifications from 'expo-notifications';
import { AndroidImportance } from 'expo-notifications';
import * as TaskManager from 'expo-task-manager';
import { type Resume, alertes } from '../domain';
import { charger } from '../application/marche';
import { ajouterAlertesVues, lireAlertesVues, lireReglages } from './stockage';
import { SOURCES } from './sources';

const TACHE = 'verifier-marche';
const CANAL = 'marche';

Notifications.setNotificationHandler({
  handleNotification: async () => ({ shouldShowBanner: true, shouldShowList: true, shouldPlaySound: true, shouldSetBadge: false }),
});

/** Envoie les alertes nouvelles. Renvoie le nombre envoyé. */
export async function prevenir(resumes: Resume[]): Promise<number> {
  if (Platform.OS === 'web' || !lireReglages().alertes) return 0;
  const nouvelles = alertes(resumes, lireAlertesVues());
  for (const a of nouvelles) {
    await Notifications.scheduleNotificationAsync({ content: { title: a.titre, body: a.texte }, trigger: Platform.OS === 'android' ? { channelId: CANAL } : null });
  }
  ajouterAlertesVues(nouvelles.map((a) => a.cle));
  return nouvelles.length;
}

if (Platform.OS !== 'web') {
  TaskManager.defineTask(TACHE, async () => {
    try {
      await prevenir((await charger(SOURCES)).resumes);
      return BackgroundTask.BackgroundTaskResult.Success;
    } catch {
      return BackgroundTask.BackgroundTaskResult.Failed;
    }
  });
}

/** Demande l'autorisation et active la tâche de fond ; à appeler au lancement. */
export async function activerAlertes(): Promise<boolean> {
  if (Platform.OS === 'web') return false;
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync(CANAL, { name: 'Marché', importance: AndroidImportance.HIGH });
  }
  const { granted } = await Notifications.requestPermissionsAsync();
  if (!(await TaskManager.isTaskRegisteredAsync(TACHE))) {
    await BackgroundTask.registerTaskAsync(TACHE, { minimumInterval: 15 });
  }
  return granted;
}
