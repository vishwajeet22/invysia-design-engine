"use client";

import React, { useEffect, useRef } from 'react';

const CosmicBackground = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let animationFrameId;
    let stars = [];
    let backgroundGradient;
    let nebulaGradient;

    // Set canvas size
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      createGradients(); // Recreate gradients on resize
    };

    const createGradients = () => {
      // Create cosmic gradient background
      backgroundGradient = ctx.createRadialGradient(
        canvas.width / 2,
        canvas.height / 2,
        0,
        canvas.width / 2,
        canvas.height / 2,
        canvas.width
      );
      backgroundGradient.addColorStop(0, '#0a0e27');
      backgroundGradient.addColorStop(0.5, '#1a1435');
      backgroundGradient.addColorStop(1, '#0d0221');

      // Nebula gradient
      nebulaGradient = ctx.createRadialGradient(
        canvas.width * 0.3,
        canvas.height * 0.4,
        0,
        canvas.width * 0.3,
        canvas.height * 0.4,
        canvas.width * 0.5
      );
      nebulaGradient.addColorStop(0, '#4a148c');
      nebulaGradient.addColorStop(0.5, '#1565c0');
      nebulaGradient.addColorStop(1, 'transparent');
    };

    window.addEventListener('resize', resizeCanvas);
    resizeCanvas(); // Initial call

    // Star class
    class Star {
      constructor() {
        this.reset();
      }

      reset() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.z = Math.random() * canvas.width;
        this.size = Math.random() * 2;
        this.speed = Math.random() * 0.5 + 0.1;
      }

      update() {
        this.z -= this.speed;
        if (this.z <= 0) {
          this.reset();
          this.z = canvas.width;
        }
      }

      draw() {
        const x = (this.x - canvas.width / 2) * (canvas.width / this.z);
        const y = (this.y - canvas.height / 2) * (canvas.width / this.z);
        const s = this.size * (canvas.width / this.z);

        const centerX = canvas.width / 2 + x;
        const centerY = canvas.height / 2 + y;

        // Only draw if on screen
        if (centerX >= 0 && centerX <= canvas.width && centerY >= 0 && centerY <= canvas.height) {
          const opacity = Math.min(1, (canvas.width - this.z) / (canvas.width * 0.3));

          ctx.beginPath();
          ctx.fillStyle = `rgba(255, 255, 255, ${opacity})`;
          ctx.arc(centerX, centerY, s, 0, Math.PI * 2);
          ctx.fill();

          // Add glow for larger stars - OPTIMIZATION: Only for very large stars or remove to improve perf
          if (s > 1.5) { // Increased threshold from 1
            ctx.shadowBlur = 10;
            ctx.shadowColor = 'white';
            ctx.fill();
            ctx.shadowBlur = 0;
          }
        }
      }
    }

    // Create stars - OPTIMIZATION: Reduced count
    for (let i = 0; i < 150; i++) { // Reduced from 300
      stars.push(new Star());
    }

    // Animation loop
    const animate = () => {
      // Draw background using cached gradient
      if (backgroundGradient) {
          ctx.fillStyle = backgroundGradient;
          ctx.fillRect(0, 0, canvas.width, canvas.height);
      }

      // Add some nebula clouds
      if (nebulaGradient) {
          ctx.globalAlpha = 0.1;
          ctx.fillStyle = nebulaGradient;
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          ctx.globalAlpha = 1;
      }

      // Update and draw stars
      stars.forEach(star => {
        star.update();
        star.draw();
      });

      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    // Cleanup
    return () => {
      window.removeEventListener('resize', resizeCanvas);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: -1,
      }}
    />
  );
};

export default CosmicBackground;
