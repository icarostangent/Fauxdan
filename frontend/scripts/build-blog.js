const fs = require('fs')
const path = require('path')

// Path to markdown files and target file
const markdownDir = path.join(__dirname, '../src/data/markdown')
const targetFile = path.join(__dirname, '../src/data/blogData.ts')

// Function to automatically discover all markdown files
function getMarkdownFiles() {
  if (!fs.existsSync(markdownDir)) {
    console.log('Markdown directory not found, creating empty blog...')
    return []
  }
  
  try {
    const files = fs.readdirSync(markdownDir)
      .filter(file => file.endsWith('.md'))
      .sort((a, b) => b.localeCompare(a)) // Sort newest first
    
    console.log(`Found ${files.length} markdown files in ${markdownDir}`)
    return files
  } catch (error) {
    console.error('Error reading markdown directory:', error)
    return []
  }
}

// Function to parse frontmatter and content
function parseMarkdownFile(content, filename) {
  const parts = content.split('---')
  
  if (parts.length < 3) {
    console.warn(`Invalid markdown format for ${filename}`)
    return null
  }
  
  const frontmatter = parts[1].trim()
  const markdownContent = parts.slice(2).join('---').trim()
  
  try {
    // Parse frontmatter (simple YAML-like parsing)
    const metadata = {}
    frontmatter.split('\n').forEach(line => {
      const [key, ...valueParts] = line.split(':')
      if (key && valueParts.length > 0) {
        const value = valueParts.join(':').trim()
        if (key === 'tags') {
          metadata[key] = value.split(',').map(tag => tag.trim())
        } else if (key === 'readTime') {
          metadata[key] = parseInt(value)
        } else if (key === 'featured') {
          metadata[key] = value.toLowerCase() === 'true'
        } else {
          metadata[key] = value
        }
      }
    })
    
    // Generate ID from filename
    const id = filename.replace(/^\d{4}-\d{2}-\d{2}-/, '').replace('.md', '')
    
    // Calculate read time if not provided
    const readTime = metadata.readTime || Math.ceil(markdownContent.split(' ').length / 200)
    
    return {
      id,
      title: metadata.title || 'Untitled',
      excerpt: metadata.excerpt || markdownContent.substring(0, 150) + '...',
      content: markdownContent,
      date: metadata.date || filename.split('-').slice(0, 3).join('-'),
      readTime,
      tags: metadata.tags || [],
      image: metadata.image,
      featured: metadata.featured || false,
      filename
    }
  } catch (error) {
    console.error(`Error parsing markdown for ${filename}:`, error)
    return null
  }
}

// Main build function
function buildBlog() {
  console.log('Building blog from markdown files...')
  
  try {
    // Automatically discover markdown files
    const markdownFiles = getMarkdownFiles()
    const posts = []
    
    // Process each markdown file
    for (const filename of markdownFiles) {
      try {
        const filePath = path.join(markdownDir, filename)
        const content = fs.readFileSync(filePath, 'utf8')
        const post = parseMarkdownFile(content, filename)
        
        if (post) {
          posts.push(post)
          console.log(`✓ Processed: ${filename}`)
        } else {
          console.warn(`⚠ Skipped: ${filename} (parsing failed)`)
        }
      } catch (error) {
        console.error(`✗ Error processing ${filename}:`, error.message)
      }
    }
    
    // Sort posts: featured first, then by date (newest first)
    posts.sort((a, b) => {
      // Featured posts first
      if (a.featured && !b.featured) return -1
      if (!a.featured && b.featured) return 1
      // Then by date (newest first)
      return new Date(b.date).getTime() - new Date(a.date).getTime()
    })
    
    // Generate the complete blogData.ts file
    const output = `// Auto-generated from markdown files - DO NOT EDIT MANUALLY
// Generated on: ${new Date().toISOString()}
// Total posts processed: ${posts.length}

export interface BlogPost {
  id: string
  title: string
  excerpt: string
  content: string
  date: string
  readTime: number
  tags: string[]
  image?: string
  featured: boolean
  filename: string
}

// This will be replaced by build-blog.js during build
export const blogPosts: BlogPost[] = ${JSON.stringify(posts, null, 2)}

export const blogData = {
  async getPosts(): Promise<BlogPost[]> {
    return blogPosts
  },
  
  async getPost(id: string): Promise<BlogPost | null> {
    return blogPosts.find(post => post.id === post.id) || null
  }
}
`
    
    // Write the output file
    fs.writeFileSync(targetFile, output)
    console.log(`✓ Generated ${targetFile} with ${posts.length} posts`)
    
    // Summary
    if (posts.length > 0) {
      const featuredPost = posts.find(p => p.featured)
      console.log('\n Blog Build Summary:')
      console.log(`   Total posts: ${posts.length}`)
      console.log(`   Featured post: ${featuredPost ? featuredPost.title : 'None (using date-based sorting)'}`)
      console.log(`   Date range: ${posts[posts.length - 1]?.date} to ${posts[0]?.date}`)
    } else {
      console.log('\n⚠ No posts were processed successfully')
    }
    
  } catch (error) {
    console.error('Error building blog:', error)
    
    // Create a fallback file even if there's an error
    const fallbackOutput = `// Auto-generated from markdown files - DO NOT EDIT MANUALLY
// Generated on: ${new Date().toISOString()}
// Error occurred during generation

export interface BlogPost {
  id: string
  title: string
  excerpt: string
  content: string
  date: string
  readTime: number
  tags: string[]
  image?: string
  featured: boolean
  filename: string
}

export const blogPosts: BlogPost[] = []

export const blogData = {
  async getPosts(): Promise<BlogPost[]> {
    return blogPosts
  },
  
  async getPost(id: string): Promise<BlogPost | null> {
    return blogPosts.find(post => post.id === post.id) || null
  }
}
`
    fs.writeFileSync(targetFile, fallbackOutput)
    console.log(`✓ Generated fallback ${targetFile}`)
  }
}

// Run the build
buildBlog()
