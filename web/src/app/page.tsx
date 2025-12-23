'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { ArrowRight, Sparkles, Zap, Shield, Image } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'

export default function HomePage() {
  const features = [
    {
      icon: <Sparkles className="w-6 h-6" />,
      title: 'AI Model Generation',
      description: 'Generate photorealistic models wearing your garments using cutting-edge AI',
    },
    {
      icon: <Image className="w-6 h-6" />,
      title: 'Virtual Try-On',
      description: 'Preserve logos and text while fitting garments onto AI models',
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: 'Instant Catalogs',
      description: 'Get print-ready PDF catalogs in minutes, not days',
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: 'Brand Consistency',
      description: 'Customize with your logo, colors, and brand identity',
    },
  ]

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-gray-950/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-lg flex items-center justify-center font-bold text-sm">
              B
            </div>
            <span className="font-semibold text-lg">Bono Studio</span>
          </div>
          <Link href="/create">
            <Button size="sm">Create Catalog</Button>
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-5xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-violet-500/10 border border-violet-500/20 rounded-full text-sm text-violet-400 mb-6">
              <Sparkles className="w-4 h-4" />
              AI-Powered Fashion Catalogs
            </div>

            <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
              Transform Flat-Lays into
              <br />
              <span className="bg-gradient-to-r from-violet-400 to-indigo-400 bg-clip-text">
                Stunning Catalogs
              </span>
            </h1>

            <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10">
              Upload your garment photos and let AI generate professional fashion models wearing your designs. Get print-ready catalogs in minutes.
            </p>

            <Link href="/create">
              <Button size="lg" className="group">
                Start Creating
                <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
          </motion.div>

          {/* Hero Image Placeholder */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="mt-16"
          >
            <Card variant="gradient" className="p-2 max-w-4xl mx-auto">
              <div className="aspect-video rounded-xl bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-6xl mb-4">👕 → 🤖 → 📄</div>
                  <p className="text-gray-500">Garment → AI Model → Catalog</p>
                </div>
              </div>
            </Card>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Everything You Need
            </h2>
            <p className="text-gray-400 max-w-xl mx-auto">
              From AI generation to final PDF, we handle the entire catalog creation process.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card variant="glass" className="h-full">
                  <div className="w-12 h-12 bg-violet-500/20 rounded-xl flex items-center justify-center text-violet-400 mb-4">
                    {feature.icon}
                  </div>
                  <h3 className="font-semibold text-white mb-2">{feature.title}</h3>
                  <p className="text-sm text-gray-400">{feature.description}</p>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <Card variant="gradient" className="p-12 text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-violet-500/10 to-indigo-500/10" />
            <div className="relative">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">
                Ready to Create Your Catalog?
              </h2>
              <p className="text-gray-400 mb-8 max-w-lg mx-auto">
                Join brands using AI to create stunning fashion catalogs faster than ever.
              </p>
              <Link href="/create">
                <Button size="lg">
                  Get Started Free
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
            </div>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 px-6">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-gradient-to-br from-violet-500 to-indigo-600 rounded flex items-center justify-center font-bold text-xs">
              B
            </div>
            <span>Bono Catalog Studio</span>
          </div>
          <p>Powered by AI</p>
        </div>
      </footer>
    </div>
  )
}
