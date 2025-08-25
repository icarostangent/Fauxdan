<template>
  <div class="blog">
    <div class="blog-header">
      <h1>Blog</h1>
      <p class="subtitle">Insights, Updates & Security Intelligence</p>
    </div>

    <div v-if="loading" class="blog-content">
      <!-- Featured Post Skeleton -->
      <div class="featured-post skeleton">
        <div class="featured-badge skeleton-badge"></div>
        <div class="featured-content">
          <div class="skeleton-title"></div>
          <div class="skeleton-excerpt"></div>
          <div class="skeleton-meta">
            <div class="skeleton-date"></div>
            <div class="skeleton-read-time"></div>
          </div>
          <div class="skeleton-button"></div>
        </div>
      </div>

      <!-- All Articles Section Skeleton -->
      <section class="all-articles">
        <div class="skeleton-section-title"></div>
        <div class="articles-grid">
          <div 
            v-for="n in 6" 
            :key="n" 
            class="article-card skeleton"
          >
            <div class="article-content">
              <div class="skeleton-article-title"></div>
              <div class="skeleton-article-excerpt"></div>
              <div class="skeleton-article-meta">
                <div class="skeleton-article-date"></div>
                <div class="skeleton-article-read-time"></div>
              </div>
              <div class="skeleton-tags">
                <div class="skeleton-tag"></div>
                <div class="skeleton-tag"></div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>

    <div v-else class="blog-content">
      <!-- Featured Post -->
      <div v-if="featuredPost" class="featured-post">
        <div class="featured-badge">Featured</div>
        <div class="featured-content">
          <h2>{{ featuredPost.title }}</h2>
          <p class="excerpt">{{ featuredPost.excerpt }}</p>
          <div class="post-meta">
            <span class="date">{{ formatDate(featuredPost.date) }}</span>
            <span class="read-time">{{ featuredPost.readTime }} min read</span>
            <div class="tags">
              <span 
                v-for="tag in featuredPost.tags" 
                :key="tag" 
                class="tag"
              >
                {{ tag }}
              </span>
            </div>
          </div>
          <router-link :to="`/blog/${featuredPost.id}`" class="read-more-btn">
            Read Full Article
          </router-link>
        </div>
      </div>

      <!-- All Articles Section -->
      <section class="all-articles">
        <h2>All Articles</h2>
        <div class="articles-grid">
          <article 
            v-for="post in allArticles" 
            :key="post.id" 
            class="article-card"
            @click="viewPost(post.id)"
          >
            <div class="article-content">
              <h3>{{ post.title }}</h3>
              <p class="excerpt">{{ post.excerpt }}</p>
              <div class="article-meta">
                <span class="date">{{ formatDate(post.date) }}</span>
                <span class="read-time">{{ post.readTime }} min read</span>
              </div>
              <div class="tags">
                <span 
                  v-for="tag in post.tags" 
                  :key="tag" 
                  class="tag"
                >
                  {{ tag }}
                </span>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { blogData, BlogPost } from '@/data/blogData'

export default defineComponent({
  name: 'BlogView',
  
  setup() {
    const router = useRouter()
    const loading = ref(true)
    const posts = ref<BlogPost[]>([])
    
    // Get featured post (either flagged as featured or first by date)
    const featuredPost = computed(() => {
      const featured = posts.value.find(post => post.featured)
      return featured || posts.value[0]
    })
    
    // Get all other posts (excluding featured)
    const allArticles = computed(() => {
      const featured = posts.value.find(post => post.featured)
      if (featured) {
        return posts.value.filter(post => !post.featured)
      }
      return posts.value.slice(1)
    })
    
    const viewPost = (postId: string) => {
      console.log('Navigating to post:', postId) // Debug log
      router.push(`/blog/${postId}`)
    }
    
    const formatDate = (dateString: string) => {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }
    
    const loadPosts = async () => {
      try {
        loading.value = true
        posts.value = await blogData.getPosts()
        console.log('Loaded posts:', posts.value) // Debug log
        console.log('Featured post:', featuredPost.value) // Debug log
        console.log('All articles:', allArticles.value) // Debug log
      } catch (error) {
        console.error('Error loading blog posts:', error)
      } finally {
        loading.value = false
      }
    }
    
    onMounted(() => {
      loadPosts()
    })
    
    return {
      loading,
      featuredPost,
      allArticles,
      viewPost,
      formatDate
    }
  }
})
</script>

<style scoped>
.blog {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.blog-header {
  text-align: center;
  margin-bottom: 60px;
  padding: 40px 0;
  border-bottom: 2px solid #e9ecef;
}

.blog-header h1 {
  font-size: 48px;
  font-weight: 700;
  margin: 0 0 20px 0;
  background: linear-gradient(135deg, #007bff, #8a2be2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  font-size: 20px;
  color: #6c757d;
  margin: 0;
}

.blog-content {
  display: grid;
  gap: 60px;
}

.featured-post {
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  border: 1px solid #dee2e6;
  border-radius: 16px;
  padding: 40px;
  position: relative;
  text-align: center;
}

.featured-badge {
  position: absolute;
  top: 20px;
  right: 20px;
  background: #007bff;
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.featured-content h2 {
  font-size: 32px;
  margin: 0 0 20px 0;
  color: #1a1a1a;
}

.featured-content .excerpt {
  font-size: 18px;
  line-height: 1.6;
  color: #495057;
  margin: 0 0 30px 0;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.post-meta {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
  font-size: 14px;
  color: #6c757d;
  flex-wrap: wrap;
}

.read-more-btn {
  background: linear-gradient(135deg, #007bff, #8a2be2);
  color: white;
  border: none;
  padding: 16px 32px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  display: inline-block;
}

.read-more-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(0, 123, 255, 0.3);
  text-decoration: none;
  color: white;
}

.all-articles h2 {
  font-size: 36px;
  font-weight: 700;
  text-align: center;
  margin: 0 0 40px 0;
  background: linear-gradient(135deg, #ffffff, #007bff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.articles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 30px;
}

.article-card {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
}

.article-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 30px rgba(0, 0, 0, 0.1);
  border-color: #007bff;
}

.article-content {
  padding: 24px;
}

.article-content h3 {
  font-size: 20px;
  margin: 0 0 15px 0;
  color: #1a1a1a;
  line-height: 1.3;
}

.article-content .excerpt {
  font-size: 14px;
  line-height: 1.6;
  color: #6c757d;
  margin: 0 0 20px 0;
}

.article-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  font-size: 12px;
  color: #6c757d;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  background: #e9ecef;
  color: #495057;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

/* Skeleton Loading Styles */
.skeleton {
  position: relative;
  overflow: hidden;
}

.skeleton::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { left: -100%; }
  100% { left: 100%; }
}

.skeleton-badge {
  width: 80px;
  height: 24px;
  background: #e9ecef;
  border-radius: 20px;
}

.skeleton-title {
  width: 80%;
  height: 32px;
  background: #e9ecef;
  border-radius: 4px;
  margin: 0 auto 20px auto;
}

.skeleton-excerpt {
  width: 90%;
  height: 18px;
  background: #e9ecef;
  border-radius: 4px;
  margin: 0 auto 20px auto;
}

.skeleton-excerpt::after {
  content: '';
  display: block;
  width: 70%;
  height: 18px;
  background: #e9ecef;
  border-radius: 4px;
  margin: 10px auto 0 auto;
}

.skeleton-meta {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 30px;
}

.skeleton-date,
.skeleton-read-time {
  width: 80px;
  height: 14px;
  background: #e9ecef;
  border-radius: 4px;
}

.skeleton-button {
  width: 160px;
  height: 48px;
  background: #e9ecef;
  border-radius: 8px;
  margin: 0 auto;
}

.skeleton-section-title {
  width: 200px;
  height: 36px;
  background: #e9ecef;
  border-radius: 4px;
  margin: 0 auto 40px auto;
}

.skeleton-article-title {
  width: 100%;
  height: 20px;
  background: #e9ecef;
  border-radius: 4px;
  margin-bottom: 15px;
}

.skeleton-article-excerpt {
  width: 100%;
  height: 14px;
  background: #e9ecef;
  border-radius: 4px;
  margin-bottom: 20px;
}

.skeleton-article-excerpt::after {
  content: '';
  display: block;
  width: 80%;
  height: 14px;
  background: #e9ecef;
  border-radius: 4px;
  margin-top: 8px;
}

.skeleton-article-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
}

.skeleton-article-date,
.skeleton-article-read-time {
  width: 60px;
  height: 12px;
  background: #e9ecef;
  border-radius: 4px;
}

.skeleton-tags {
  display: flex;
  gap: 8px;
}

.skeleton-tag {
  width: 60px;
  height: 20px;
  background: #e9ecef;
  border-radius: 20px;
}

@media (max-width: 768px) {
  .blog-header h1 {
    font-size: 36px;
  }
  
  .featured-content h2 {
    font-size: 24px;
  }
  
  .articles-grid {
    grid-template-columns: 1fr;
  }
  
  .post-meta {
    flex-direction: column;
    gap: 10px;
  }
  
  .skeleton-meta {
    flex-direction: column;
    gap: 10px;
  }
}
</style>
