// frontend/src/utils/wikiMappers.js

/**
 * Mapuj artykuł z backendu do formatu używanego przez frontend
 */
export function mapArticleToItem(article) {
  return {
    name: article.title,
    category: article.category,
    image_url: article.image_url,
    description: article.content?.description || '',
    ...article.content  // Spread reszty contentu
  };
}

/**
 * Mapuj artykuł na postać
 */
export function mapArticleToCharacter(article) {
  const content = article.content || {};
  
  return {
    name: article.title,
    description: content.description || '',
    image_url: article.image_url,
    info: {
      species: content.species || '',
      homeworld: content.homeworld || '',
      born: content.born || '',
      gender: content.gender || '',
      height: content.height || '',
      mass: content.mass || '',
      skin_color: content.skin_color || '',
      eye_color: content.eye_color || '',
      hair_color: content.hair_color || '',
    },
    affiliations: content.affiliations || [],
    abilities: content.abilities || []
  };
}

/**
 * Mapuj artykuł na planetę
 */
export function mapArticleToPlanet(article) {
  const content = article.content || {};
  
  return {
    name: article.title,
    image_url: article.image_url,
    description: content.description || '',
    system: content.system || '',
    sector: content.sector || '',
    climate: content.climate || '',
    terrain: content.terrain || '',
    population: content.population || ''
  };
}