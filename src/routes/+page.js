import { redirect } from '@sveltejs/kit';

export function load() {
  throw redirect(307, '/open-offers'); // Use 307 for temporary redirect
}